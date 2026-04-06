# Connector Template

Annotated template showing the structure of a generated Data Lens connector.
Use this as a structural guide — adapt the specifics to the user's schema and
database type.

## Directory Structure

```
my-connector/
├── __init__.py          # Operator + handler + transform
├── fiftyone.yml         # Plugin manifest
└── requirements.txt     # Python driver dependency
```

## fiftyone.yml

```yaml
name: "@myorg/my-connector"
type: plugin
operators:
  - my_connector
secrets:
  - MY_CONNECTION_STRING    # One entry per secret the connector needs
```

**Naming conventions:**
- `name`: scoped package name — `@org/connector-name` or `@voxel51/datalens_dbtype`
- `operators`: list of operator class names (snake_case, matching `OperatorConfig.name`)
- `secrets`: environment variable names the operator accesses via `ctx.secret()`

## requirements.txt

```
psycopg[binary]>=3.0
```

Only include the database driver. The FiftyOne SDK is already available at runtime.

## __init__.py — Full Annotated Template

```python
import contextlib
import json
from dataclasses import dataclass
from typing import Generator, Optional

import fiftyone as fo
import fiftyone.operators as foo
import fiftyone.operators.types as types
from fiftyone.operators.data_lens import (
    DataLensOperator,
    DataLensSearchRequest,
    DataLensSearchResponse,
)
from fiftyone.operators.data_lens.utils import filter_fields_for_type

# ── Database driver import ──────────────────────────────────────────
# Adapt to the target database:
#   PostgreSQL:  import psycopg; from psycopg.rows import dict_row
#   BigQuery:    from google.cloud import bigquery
#   MySQL:       import mysql.connector
#   SQLite:      import sqlite3
import psycopg
from psycopg.rows import dict_row


# ── Data models (optional) ──────────────────────────────────────────
# Typed wrappers for query parameters and result rows.
# These are optional but improve readability for complex schemas.

@dataclass
class QueryParams:
    """Validated query parameters extracted from search_params.

    One field per filterable column. Field names must match the keys
    defined in resolve_input().
    """
    weather: str       # enum filter — "all" means no filter
    scene: str         # enum filter
    # Add more fields as needed


@dataclass
class QueryResultRow:
    """Typed representation of a single database row.

    Field names must match the column names (or aliases) in the SQL query.
    """
    path: str
    weather: str
    scene: str
    detections: list[dict]
    # Add more fields as needed


# ── Handler class ───────────────────────────────────────────────────
# Encapsulates connection management, query execution, and sample
# transformation. Implements context manager for clean resource lifecycle.

class MyHandler:
    def __init__(self, connection_string: str):
        self._connection_string = connection_string
        self._conn = None

    def __enter__(self):
        self._conn = psycopg.connect(self._connection_string)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._conn is not None:
            self._conn.__exit__(exc_type, exc_val, exc_tb)
        self._conn = None

    # ── Batching loop ───────────────────────────────────────────────
    # Core iteration: query → transform → batch → yield responses.
    # This method's structure is the same for every connector.

    def iter_batches(
        self,
        request: DataLensSearchRequest,
    ) -> Generator[DataLensSearchResponse, None, None]:
        buffer = []
        for sample_dict in self._iter_samples(request):
            buffer.append(sample_dict)

            if len(buffer) >= request.batch_size:
                yield DataLensSearchResponse(
                    result_count=len(buffer),
                    query_result=buffer,
                )
                buffer = []

        if buffer:
            yield DataLensSearchResponse(
                result_count=len(buffer),
                query_result=buffer,
            )

    # ── Query execution ─────────────────────────────────────────────
    # Streams rows from the database one at a time, transforming each
    # into a serialized fo.Sample dict.

    def _iter_samples(
        self,
        request: DataLensSearchRequest,
    ) -> Generator[dict, None, None]:
        query, args = self._generate_query(request)
        with self._conn.cursor(row_factory=dict_row) as cursor:
            with contextlib.closing(
                cursor.stream(query, args, size=request.batch_size)
            ) as row_generator:
                for row in row_generator:
                    yield self._transform_sample(
                        QueryResultRow(
                            **filter_fields_for_type(row, QueryResultRow)
                        )
                    )

    # ── Query builder ───────────────────────────────────────────────
    # Builds parameterized SQL from the user's search_params.
    #
    # KEY RULES:
    # - Always use parameterized queries (never f-string interpolation
    #   for user values)
    # - Use the conditional WHERE pattern for "all" option:
    #     AND (1={1 if param == "all" else 0} OR column = %s)
    # - Always pass all params even if unused (positional binding)

    def _generate_query(
        self,
        request: DataLensSearchRequest,
    ) -> tuple[str, tuple]:
        params = QueryParams(
            **filter_fields_for_type(request.search_params, QueryParams)
        )

        query = """
        SELECT
            samples.path,
            samples.weather,
            samples.scene,
            COALESCE((
                SELECT JSON_AGG(
                    JSON_BUILD_OBJECT(
                        'label', labels.label,
                        'bbox', labels.bbox
                    )
                )
                FROM my_labels labels
                WHERE labels.sample_id = samples.id
            ), '[]'::json) AS detections
        FROM
            my_samples samples
        WHERE
            1=1
        AND (1={skip_weather} OR samples.weather = %s)
        AND (1={skip_scene} OR samples.scene = %s)
        """.format(
            skip_weather=1 if params.weather == "all" else 0,
            skip_scene=1 if params.scene == "all" else 0,
        )

        return query, (params.weather, params.scene)

    # ── Sample transform ────────────────────────────────────────────
    # Maps a database row to a serialized fo.Sample dict.
    #
    # This is the most connector-specific part. Key considerations:
    # - filepath: construct the full path (prefix + column value)
    # - metadata: set image dimensions if known (required for bbox
    #   normalization)
    # - labels: map to the correct FiftyOne label type
    # - bounding boxes: normalize to [0,1] range as [x, y, w, h]

    def _transform_sample(self, row: QueryResultRow) -> dict:
        return fo.Sample(
            filepath=f"gs://my-bucket/images/{row.path}",
            metadata=fo.ImageMetadata(width=1920, height=1080),
            weather=fo.Classification(label=row.weather),
            scene=fo.Classification(label=row.scene),
            detections=self._build_detections(row.detections),
        ).to_dict()

    # ── Detection builder ───────────────────────────────────────────
    # Converts raw bounding box data to fo.Detections.
    #
    # FiftyOne bounding box format: [x, y, width, height] normalized
    # to [0, 1] relative to image dimensions.
    #
    # Common source formats:
    #   [x1, y1, x2, y2] pixels → normalize and convert to [x, y, w, h]
    #   [cx, cy, w, h] pixels   → convert center to top-left, normalize
    #   [x, y, w, h] pixels     → just normalize

    def _build_detections(self, raw_detections: list[dict]) -> fo.Detections:
        if not raw_detections:
            return fo.Detections(detections=[])

        width, height = 1920, 1080  # Use actual image dims if per-sample

        return fo.Detections(
            detections=[
                fo.Detection(
                    label=det["label"],
                    bounding_box=[
                        det["bbox"]["x1"] / width,           # x (normalized)
                        det["bbox"]["y1"] / height,          # y (normalized)
                        (det["bbox"]["x2"] - det["bbox"]["x1"]) / width,   # w
                        (det["bbox"]["y2"] - det["bbox"]["y1"]) / height,  # h
                    ],
                )
                for det in raw_detections
                if "bbox" in det
            ]
        )


# ── Operator class ──────────────────────────────────────────────────
# The DataLensOperator subclass. This is the entry point registered
# with FiftyOne's plugin system.

class MyConnector(DataLensOperator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="my_connector",
            label="My Data Source",
            description="Browse and import samples from my database",
            execute_as_generator=True,  # REQUIRED for Data Lens
            unlisted=True,              # Hide from operator browser
        )

    # ── Input form ──────────────────────────────────────────────────
    # Defines the filter UI shown in the Data Lens panel.
    # Each input becomes a key in request.search_params.
    #
    # Common patterns:
    #   inputs.enum(...)  — dropdown filter with known values
    #   inputs.str(...)   — free-text search
    #   inputs.bool(...)  — toggle for optional behavior
    #   inputs.int(...)   — numeric threshold/limit
    #
    # Use inputs.view("header", types.HeaderView(...)) for section headers.

    def resolve_input(self, ctx: foo.ExecutionContext):
        inputs = types.Object()

        inputs.enum(
            "weather",
            ["all", "clear", "rainy", "snowy", "foggy"],
            label="Weather",
            description="Filter by weather condition",
            default="all",
        )

        inputs.enum(
            "scene",
            ["all", "urban", "highway", "rural"],
            label="Scene",
            description="Filter by scene type",
            default="all",
        )

        return types.Property(inputs)

    # ── Search handler ──────────────────────────────────────────────
    # Delegates to the handler class. This method's structure is the
    # same for every connector — only the handler class changes.

    def handle_lens_search_request(
        self,
        request: DataLensSearchRequest,
        ctx: foo.ExecutionContext,
    ) -> Generator[DataLensSearchResponse, None, None]:
        connection_string = ctx.secret("MY_CONNECTION_STRING")
        with MyHandler(connection_string) as handler:
            for response in handler.iter_batches(request):
                yield response


# ── Registration ────────────────────────────────────────────────────
def register(p):
    p.register(MyConnector)
```

## Adaptation Checklist

When generating a connector from this template, customize:

- [ ] **Database driver** — import and connection setup in handler `__enter__`
- [ ] **QueryParams dataclass** — one field per filterable search parameter
- [ ] **QueryResultRow dataclass** — one field per selected column
- [ ] **`_generate_query()`** — SQL matching the user's schema and table names
- [ ] **`_transform_sample()`** — field mapping to `fo.Sample` with correct types
- [ ] **`_build_detections()`** — coordinate normalization matching the source format (or remove if no spatial data)
- [ ] **`resolve_input()`** — filter fields with correct enum values
- [ ] **`config` property** — operator name and label
- [ ] **`fiftyone.yml`** — plugin name, operator name, secrets list
- [ ] **`requirements.txt`** — correct database driver package

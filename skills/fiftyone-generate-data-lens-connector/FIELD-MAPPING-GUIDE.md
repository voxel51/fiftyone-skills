# Field Mapping Guide

Rules for mapping database column types to FiftyOne field types when generating
Data Lens connectors.

## Scalar Fields

| Database Type | FiftyOne Field | Construction |
|---------------|----------------|--------------|
| `VARCHAR`, `TEXT`, `STRING` | `str` | `sample["field"] = value` |
| `INT`, `INTEGER`, `BIGINT` | `int` | `sample["field"] = value` |
| `FLOAT`, `DOUBLE`, `DECIMAL`, `NUMERIC` | `float` | `sample["field"] = value` |
| `BOOLEAN`, `BOOL` | `bool` | `sample["field"] = value` |
| `DATE`, `TIMESTAMP`, `DATETIME` | `datetime` | `sample["field"] = datetime_value` |

## Media Path (filepath)

The `filepath` field is **required** on every `fo.Sample`. It must be a string
pointing to the media file — local path or cloud URI.

**Common patterns:**

| Source Column | Construction | Example |
|---------------|-------------|---------|
| Full absolute path | Use directly | `/data/images/001.jpg` |
| Full cloud URI | Use directly | `s3://bucket/images/001.jpg` |
| Relative filename | Prepend base path | `f"gs://bucket/path/{row.filename}"` |
| ID-based | Construct from pattern | `f"s3://bucket/{row.split}/{row.id}.jpg"` |

**Always ask the user:**
1. Is the path absolute or does it need a prefix?
2. What's the base path / bucket URI?
3. Does the path pattern vary (e.g., by split or date)?

## Image Metadata

If image dimensions are known (fixed or per-sample), set `metadata`:

```python
# Fixed dimensions (all images same size)
fo.Sample(
    filepath=...,
    metadata=fo.ImageMetadata(width=1920, height=1080),
)

# Per-sample dimensions (from database columns)
fo.Sample(
    filepath=...,
    metadata=fo.ImageMetadata(width=row.width, height=row.height),
)
```

Metadata is **required** if you need to normalize bounding box coordinates from
pixel values. If dimensions aren't available, use `sample.compute_metadata()`
(slower — hits the media file).

## Classification Fields

Single-label categorical columns map to `fo.Classification`:

```python
fo.Classification(label=row.weather)        # "sunny", "rainy", etc.
fo.Classification(label=row.scene_type)     # "urban", "highway", etc.
fo.Classification(label=str(row.category))  # Ensure string type
```

**When to use Classification:**
- Column has a small set of categorical values
- Column represents a single label per sample
- Column is a good candidate for an enum filter in `resolve_input()`

**Handling NULL:** Check before constructing:
```python
weather=fo.Classification(label=row.weather) if row.weather else None,
```

## Classifications (Multi-label)

If a sample can have multiple categorical labels:

```python
fo.Classifications(
    classifications=[
        fo.Classification(label=tag)
        for tag in row.tags  # e.g., ["outdoor", "daytime", "urban"]
    ]
)
```

## Detection Fields

Bounding box annotations map to `fo.Detection` / `fo.Detections`.

### Bounding Box Format

FiftyOne uses **normalized [x, y, width, height]** where all values are in `[0, 1]`
relative to image dimensions:

```
[x, y, width, height]
 │  │    │       │
 │  │    │       └── box height / image height
 │  │    └────────── box width / image width
 │  └─────────────── top-left y / image height
 └────────────────── top-left x / image width
```

### Conversion from Common Formats

#### [x1, y1, x2, y2] in pixels (most common)
```python
bounding_box = [
    x1 / img_width,
    y1 / img_height,
    (x2 - x1) / img_width,
    (y2 - y1) / img_height,
]
```

#### [cx, cy, w, h] in pixels (YOLO-style, not normalized)
```python
bounding_box = [
    (cx - w / 2) / img_width,
    (cy - h / 2) / img_height,
    w / img_width,
    h / img_height,
]
```

#### [cx, cy, w, h] already normalized (YOLO format)
```python
bounding_box = [
    cx - w / 2,
    cy - h / 2,
    w,
    h,
]
```

#### [x, y, w, h] in pixels
```python
bounding_box = [
    x / img_width,
    y / img_height,
    w / img_width,
    h / img_height,
]
```

### Detection Construction

```python
fo.Detection(
    label=det["category"],
    bounding_box=[...],                     # normalized [x, y, w, h]
    confidence=det.get("confidence"),       # optional float
    # Any additional attributes:
    occluded=det.get("occluded", False),
    truncated=det.get("truncated", False),
)
```

### Detections from JSON Blob Column

Common pattern — detections stored as a JSON array in a single column:

```python
def _build_detections(self, raw: list[dict], width: int, height: int) -> fo.Detections:
    if not raw:
        return fo.Detections(detections=[])

    return fo.Detections(
        detections=[
            fo.Detection(
                label=det["label"],
                bounding_box=[
                    det["x1"] / width,
                    det["y1"] / height,
                    (det["x2"] - det["x1"]) / width,
                    (det["y2"] - det["y1"]) / height,
                ],
            )
            for det in raw
            if det.get("x1") is not None  # Skip entries without bbox
        ]
    )
```

### Detections from a JOIN Table

When labels are in a separate table, use a subquery to aggregate:

```sql
-- PostgreSQL
SELECT
    s.*,
    COALESCE((
        SELECT JSON_AGG(JSON_BUILD_OBJECT(
            'label', l.label,
            'x1', l.x1, 'y1', l.y1,
            'x2', l.x2, 'y2', l.y2
        ))
        FROM labels l WHERE l.sample_id = s.id
    ), '[]'::json) AS detections
FROM samples s

-- BigQuery
SELECT
    s.*,
    ARRAY_AGG(STRUCT(l.label, l.x1, l.y1, l.x2, l.y2)) AS detections
FROM samples s
LEFT JOIN labels l ON l.sample_id = s.id
GROUP BY s.id

-- MySQL
SELECT
    s.*,
    COALESCE((
        SELECT JSON_ARRAYAGG(JSON_OBJECT(
            'label', l.label,
            'x1', l.x1, 'y1', l.y1,
            'x2', l.x2, 'y2', l.y2
        ))
        FROM labels l WHERE l.sample_id = s.id
    ), JSON_ARRAY()) AS detections
FROM samples s
```

## Keypoint Fields

Keypoint annotations (pose, landmarks):

```python
fo.Keypoint(
    label="person",
    points=[(x1/w, y1/h), (x2/w, y2/h), ...],  # normalized (x, y) pairs
    # Use (0, 0) or None for occluded/missing keypoints
)

# Multiple keypoint instances per sample
fo.Keypoints(
    keypoints=[fo.Keypoint(...), fo.Keypoint(...)]
)
```

## Segmentation Fields

### Semantic Segmentation (pixel mask)
```python
import numpy as np

# mask: 2D numpy array of integer class IDs, same size as image
fo.Segmentation(mask=mask_array)
```

### Instance Segmentation (per-detection mask)
```python
fo.Detection(
    label="car",
    bounding_box=[...],
    mask=mask_array,  # 2D bool array, size of bounding box region
)
```

Segmentation data is rarely stored directly in SQL databases. More commonly
the database stores a path to a mask file — load it during transform:

```python
mask_path = f"gs://bucket/masks/{row.mask_filename}"
# Note: mask loading may require additional handling depending on storage
```

## Polyline Fields

For polygon annotations:

```python
fo.Polyline(
    label="road",
    points=[[(x1/w, y1/h), (x2/w, y2/h), ...]],  # list of list of (x,y)
    closed=True,    # True for polygons, False for polylines
    filled=True,    # True for filled polygons
)
```

## GeoLocation Fields

For geospatial data:

```python
fo.GeoLocation(
    point=[longitude, latitude],  # Note: [lng, lat] order (GeoJSON convention)
)
```

## Handling NULLs

Database columns are often nullable. Always guard label construction:

```python
fo.Sample(
    filepath=...,
    # Guard nullable Classification fields
    weather=fo.Classification(label=row.weather) if row.weather else None,
    # Guard nullable Detection fields
    detections=self._build_detections(row.detections) if row.detections else None,
    # Scalar fields can be None directly
    score=row.score,  # None is fine for scalars
)
```

## Column Name → FiftyOne Field Name

FiftyOne field names must be valid Python identifiers. Convert as needed:

| Database Column | FiftyOne Field | Rule |
|-----------------|----------------|------|
| `time_of_day` | `time_of_day` | Already valid |
| `TimeOfDay` | `time_of_day` | Convert to snake_case |
| `bbox-x1` | `bbox_x1` | Replace hyphens with underscores |
| `class` | `label_class` | Avoid Python reserved words |
| `id` | Keep as scalar | Don't use `id` for Classification (it's a built-in) |

## Decision Tree: Which FiftyOne Type?

```
Is this column the media file path?
  → YES: filepath (str)

Is this a single categorical value per sample?
  → YES: fo.Classification

Is this a list of categorical values per sample?
  → YES: fo.Classifications

Does this column contain bounding box coordinates?
  → YES: fo.Detection / fo.Detections

Does this column contain keypoint coordinates?
  → YES: fo.Keypoint / fo.Keypoints

Does this column contain polygon coordinates?
  → YES: fo.Polyline / fo.Polylines

Does this column contain a segmentation mask or path to one?
  → YES: fo.Segmentation

Does this column contain lat/lng coordinates?
  → YES: fo.GeoLocation

Is this a numeric, string, bool, or date value?
  → YES: Use as a scalar field directly on the sample
```

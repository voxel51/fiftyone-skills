# Python Operator Development

## Contents
- [Operator Anatomy](#operator-anatomy)
- [OperatorConfig Options](#operatorconfig-options)
- [Execution Context](#execution-context-ctx)
- [Input Types Reference](#input-types-reference)
- [Execution Patterns](#execution-patterns)
- [Custom Runs (Auditable Operations)](#custom-runs-auditable-operations)
- [Using Execution Store](#using-execution-store)
- [Output Display](#output-display)
- [Placement (UI Buttons)](#placement-ui-buttons)
- [Debugging Operators](#debugging-operators)
- [Complete Example](#complete-example-label-exporter)

---

## Operator Anatomy

```python
import fiftyone.operators as foo
import fiftyone.operators.types as types


class MyOperator(foo.Operator):
    @property
    def config(self):
        """Operator metadata and configuration"""
        return foo.OperatorConfig(
            name="my_operator",
            label="My Operator",
            description="What this operator does",
            dynamic=False,
            execute_as_generator=False,
            unlisted=False,
            allow_immediate_execution=True,
            allow_delegated_execution=False,
        )

    def resolve_input(self, ctx):
        """Define the input form shown to users"""
        inputs = types.Object()
        # Add input fields
        return types.Property(inputs)

    def resolve_delegation(self, ctx):
        """Decide if this should run in background (optional)"""
        return len(ctx.view) > 1000

    def execute(self, ctx):
        """Main execution logic"""
        # Access parameters: ctx.params["param_name"]
        # Access dataset: ctx.dataset
        # Access view: ctx.view
        return {"result": "value"}

    def resolve_output(self, ctx):
        """Define output display form (optional)"""
        outputs = types.Object()
        outputs.str("result", label="Result")
        return types.Property(outputs)

    def resolve_placement(self, ctx):
        """Add button/menu to App UI (optional)"""
        return types.Placement(
            types.Places.SAMPLES_GRID_ACTIONS,
            types.Button(label="Run", icon="/assets/icon.svg")
        )


def register(p):
    p.register(MyOperator)
```

## OperatorConfig Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `name` | str | Required | Operator URI component (snake_case) |
| `label` | str | Required | Display name in operator browser |
| `description` | str | "" | Description shown in browser |
| `dynamic` | bool | False | Recalculate inputs after changes |
| `execute_as_generator` | bool | False | Yield progress updates |
| `unlisted` | bool | False | Hide from operator browser |
| `allow_immediate_execution` | bool | True | Run synchronously |
| `allow_delegated_execution` | bool | False | Run in background |
| `allow_distributed_execution` | bool | False | Run across workers |

## Execution Context (ctx)

The context object provides access to everything:

```python
def execute(self, ctx):
    # User input parameters
    param = ctx.params["param_name"]

    # Current dataset
    dataset = ctx.dataset

    # Current view (filtered dataset)
    view = ctx.view

    # Selected sample IDs (from App)
    selected = ctx.selected

    # Plugin secrets (from environment)
    api_key = ctx.secrets["API_KEY"]

    # Trigger other operators
    ctx.trigger("@plugin/other_operator", params={})

    # Get target view (respects user selection)
    target = ctx.target_view()

    # Set progress (for delegated execution with callback)
    ctx.set_progress(progress=0.5, label="Processing...")

    # Set progress (for generator operators - use yield)
    # yield ctx.trigger("set_progress", {"progress": 0.5, "label": "..."})
```

## Input Types Reference

### Basic Types

```python
def resolve_input(self, ctx):
    inputs = types.Object()

    # String input
    inputs.str(
        "text_field",
        label="Text Field",
        description="Enter some text",
        required=True,
        default="default value"
    )

    # Integer input
    inputs.int(
        "number_field",
        label="Number",
        default=10,
        min=0,
        max=100
    )

    # Float input
    inputs.float(
        "float_field",
        label="Decimal",
        default=0.5,
        min=0.0,
        max=1.0
    )

    # Boolean checkbox
    inputs.bool(
        "checkbox_field",
        label="Enable Feature",
        default=True
    )

    return types.Property(inputs)
```

### Selection Types

```python
def resolve_input(self, ctx):
    inputs = types.Object()

    # Dropdown enum
    inputs.enum(
        "choice_field",
        values=["option1", "option2", "option3"],
        label="Select Option",
        default="option1"
    )

    # Radio buttons (enum with radio view)
    inputs.enum(
        "radio_field",
        values=["small", "medium", "large"],
        label="Size",
        view=types.RadioGroup()
    )

    # Multi-select
    inputs.list(
        "multi_select",
        types.String(),
        label="Select Multiple",
        default=[]
    )

    return types.Property(inputs)
```

### Dataset/View Types

```python
def resolve_input(self, ctx):
    inputs = types.Object()

    # Target view selector (current view vs entire dataset)
    inputs.view_target(ctx)

    # Field selector from dataset
    field_choices = types.Dropdown()
    for field in ctx.dataset.get_field_schema():
        field_choices.add_choice(field, label=field)
    inputs.enum(
        "field_name",
        field_choices.values(),
        label="Select Field"
    )

    return types.Property(inputs)
```

### File Types

```python
def resolve_input(self, ctx):
    inputs = types.Object()

    # File upload
    inputs.file(
        "input_file",
        label="Upload File",
        types=[".json", ".csv"]  # Allowed extensions
    )

    # Directory path
    inputs.str(
        "directory",
        label="Directory Path",
        view=types.DirectoryView()
    )

    return types.Property(inputs)
```

### Dynamic Inputs

For inputs that depend on other inputs:

```python
@property
def config(self):
    return foo.OperatorConfig(
        name="dynamic_operator",
        label="Dynamic Operator",
        dynamic=True  # Enable dynamic inputs
    )

def resolve_input(self, ctx):
    inputs = types.Object()

    inputs.enum(
        "operation",
        values=["classify", "detect", "segment"],
        label="Operation Type"
    )

    # Show different inputs based on selection
    operation = ctx.params.get("operation", "classify")

    if operation == "classify":
        inputs.int("num_classes", label="Number of Classes", default=10)
    elif operation == "detect":
        inputs.float("threshold", label="Confidence Threshold", default=0.5)
    elif operation == "segment":
        inputs.bool("include_masks", label="Include Masks", default=True)

    return types.Property(inputs)
```

## Execution Patterns

### Simple Execution

```python
def execute(self, ctx):
    field = ctx.params["field_name"]

    for sample in ctx.view:
        sample[field] = compute_something(sample)
        sample.save()

    return {"processed": len(ctx.view)}
```

### Generator Execution (Progress Updates)

```python
@property
def config(self):
    return foo.OperatorConfig(
        name="progress_operator",
        execute_as_generator=True
    )

def execute(self, ctx):
    total = len(ctx.view)

    for i, sample in enumerate(ctx.view):
        # Process sample
        process(sample)
        sample.save()

        # Yield progress to UI
        yield ctx.trigger(
            "set_progress",
            {"progress": (i + 1) / total, "label": f"Processing {i + 1}/{total}"}
        )

    yield {"status": "complete", "processed": total}
```

### Delegated Execution (Background)

```python
@property
def config(self):
    return foo.OperatorConfig(
        name="background_operator",
        allow_delegated_execution=True,
        allow_immediate_execution=True
    )

def resolve_delegation(self, ctx):
    # Delegate for large datasets
    return len(ctx.view) > 1000

def execute(self, ctx):
    # Same execution logic - runs in background automatically
    for sample in ctx.view:
        process(sample)
        sample.save()
    return {}
```

### Using External APIs

```python
def execute(self, ctx):
    import requests

    # Get API key from secrets
    api_key = ctx.secrets["MY_API_KEY"]

    results = []
    for sample in ctx.view:
        # Call external API
        response = requests.post(
            "https://api.example.com/analyze",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"image_url": sample.filepath}
        )

        # Store results
        sample["api_result"] = response.json()
        sample.save()
        results.append(response.json())

    return {"results": results}
```

## Custom Runs (Auditable Operations)

Use Custom Runs for operations that need auditability and reproducibility:

```python
from datetime import datetime

class AuditableOperator(foo.Operator):
    version = "v1"

    @property
    def config(self):
        return foo.OperatorConfig(
            name="auditable_operator",
            label="Auditable Operator",
            allow_delegated_execution=True,
        )

    def execute(self, ctx):
        # Create unique run key (must be valid Python identifier)
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        run_key = f"my_plugin_{self.config.name}_{self.version}_{timestamp}"

        # Initialize run config (light metadata, <16MB)
        run_config = ctx.dataset.init_run(
            operator=self.config.name,
            version=self.version,
            params=dict(ctx.params),
            dataset_name=ctx.dataset.name,
        )

        # Perform operation
        result = self._process_samples(ctx)

        # Initialize run results (can be large, stored in GridFS)
        run_results = ctx.dataset.init_run_results(run_key)
        run_results.summary = result.get("summary", {})
        run_results.processed_count = result.get("count", 0)

        # Register run with config and results
        ctx.dataset.register_run(run_key, run_config, results=run_results)

        return result

    def _process_samples(self, ctx):
        # Processing logic here
        return {"summary": {...}, "count": len(ctx.target_view())}
```

### Managing Custom Runs

```python
# List all runs
run_keys = dataset.list_runs()

# Get run info (config)
run_info = dataset.get_run_info(run_key)

# Load run results
results = dataset.load_run_results(run_key)

# Update run config
new_config = dataset.init_run(note="Updated config")
dataset.update_run_config(run_key, new_config)

# Rename or delete runs
dataset.rename_run(run_key, f"{run_key}-archived")
dataset.delete_run(run_key)
```

### Run Key Convention

Run keys **must be valid Python identifiers** (letters, numbers, underscores only):

```
<namespace>_<operator>_<version>_<timestamp>

# Examples:
my_plugin_process_data_v1_20250122T120000Z
my_plugin_export_labels_v2_20250122T120500Z
```

**Note:** Slashes are NOT allowed in run keys.

## Using Execution Store

Use `ctx.store()` for persistent data across sessions:

```python
class CachedOperator(foo.Operator):
    version = "v1"

    def _get_store_key(self, ctx):
        """Generate unique store key."""
        plugin_name = self.config.name.split("/")[-1]
        return f"{plugin_name}_{ctx.dataset._doc.id}_{self.version}"

    def execute(self, ctx):
        store = ctx.store(self._get_store_key(ctx))

        # Check cache
        cache_key = f"result_{hash(str(ctx.params))}"
        cached = store.get(cache_key)

        if cached and self._is_valid(cached, ctx):
            return cached["result"]

        # Compute and cache
        result = self._compute(ctx)

        store.set(cache_key, {
            "result": result,
            "cached_at": time.time(),
            "dataset_size": len(ctx.dataset),
        })

        return result

    def _is_valid(self, cached, ctx):
        """Check cache validity."""
        cached_size = cached.get("dataset_size", 0)
        return abs(len(ctx.dataset) - cached_size) < cached_size * 0.05
```

### Store API Quick Reference

```python
store = ctx.store("my_store")

store.get(key)                    # Returns value or None
store.set(key, value)             # Persist value
store.set(key, value, ttl=3600)   # Expire in 1 hour
store.has(key)                    # Returns bool
store.delete(key)                 # Returns bool
store.list_keys()                 # Returns list of keys
store.clear()                     # Delete all keys
```

See [EXECUTION-STORE.md](EXECUTION-STORE.md) for advanced caching patterns.

## Output Display

```python
def resolve_output(self, ctx):
    outputs = types.Object()

    # Display results from execute()
    result = ctx.results  # Contains return value from execute()

    outputs.str(
        "status",
        label="Status",
        default=result.get("status", "complete")
    )

    outputs.int(
        "count",
        label="Processed Count",
        default=result.get("processed", 0)
    )

    # Markdown for rich output
    outputs.str(
        "summary",
        label="Summary",
        view=types.MarkdownView(),
        default=f"**Processed:** {result.get('processed', 0)} samples"
    )

    return types.Property(outputs)
```

## Displaying Plots in Output

Use `outputs.view()` with `PlotlyView` to display Plotly charts. Pass `data` (array of traces) and `layout` as **separate parameters**.

```python
def resolve_output(self, ctx):
    outputs = types.Object()

    # Plotly traces array
    data = [
        {
            "x": ["A", "B", "C"],
            "y": [10, 20, 15],
            "type": "bar",  # or "scatter", "heatmap", "pie", etc.
        }
    ]

    # Plotly layout object
    layout = {
        "title": "My Chart",
        "height": 400,
    }

    outputs.view("chart", types.PlotlyView(data=data, layout=layout))

    return types.Property(outputs)
```

## Placement (UI Buttons)

Add buttons to specific locations in the App:

```python
def resolve_placement(self, ctx):
    return types.Placement(
        types.Places.SAMPLES_GRID_ACTIONS,
        types.Button(
            label="Run My Operator",
            icon="/assets/icon.svg",
            prompt=True  # Show input form
        )
    )
```

### Available Placements

| Placement | Location |
|-----------|----------|
| `SAMPLES_GRID_ACTIONS` | Grid view action bar |
| `SAMPLES_GRID_SECONDARY_ACTIONS` | Grid view secondary actions |
| `SAMPLES_VIEWER_ACTIONS` | Sample viewer actions |
| `EMBEDDINGS_ACTIONS` | Embeddings panel actions |
| `HISTOGRAM_ACTIONS` | Histogram panel actions |
| `MAP_ACTIONS` | Map panel actions |

## Debugging Operators

### Running Server for Logs

To see Python logs from your plugin, run the server separately:

```bash
# Terminal 1: Start FiftyOne server (logs appear here)
python -m fiftyone.server.main

# Terminal 2: Open app in browser at localhost:5151
```

### Debug Patterns

```python
def execute(self, ctx):
    # Quick debugging with print (shows in server terminal)
    print(f"=== DEBUG: {self.config.name} ===")
    print(f"Params: {ctx.params}")
    print(f"Dataset: {ctx.dataset.name}")
    print(f"View size: {len(ctx.view)}")
    print(f"Selected: {ctx.selected}")

    # Structured logging
    import logging
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    logger.debug(f"Processing view with {len(ctx.target_view())} samples")

    # Inspect store contents
    store = ctx.store("my_store")
    print(f"Store keys: {store.list_keys()}")

    # ... rest of execution
```

### Common Debug Scenarios

| Issue | Debug Approach |
|-------|----------------|
| Operator not found | Check `fiftyone.yml`, run `list_operators()` |
| Params missing | Print `ctx.params` at start of `execute()` |
| Wrong view/samples | Print `len(ctx.view)`, `len(ctx.target_view())`, `ctx.selected` |
| Store not persisting | Print `store.list_keys()` before and after |
| Silent failure | Wrap in try/except, print exception |

---

## Complete Example: Label Exporter

```python
import fiftyone.operators as foo
import fiftyone.operators.types as types
import json
import os


class ExportLabels(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="export_labels",
            label="Export Labels",
            description="Export labels to JSON file",
            dynamic=True,
            execute_as_generator=True
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        # Target view selector
        inputs.view_target(ctx)

        # Label field selector
        label_fields = []
        schema = ctx.dataset.get_field_schema()
        for field_name, field in schema.items():
            if hasattr(field, "document_type"):
                label_fields.append(field_name)

        inputs.enum(
            "label_field",
            values=label_fields,
            label="Label Field",
            required=True
        )

        # Output path
        inputs.str(
            "output_path",
            label="Output File Path",
            description="Path to save JSON file",
            required=True,
            default="./labels_export.json"
        )

        # Format options
        inputs.bool(
            "include_filepath",
            label="Include File Paths",
            default=True
        )

        return types.Property(inputs)

    def execute(self, ctx):
        label_field = ctx.params["label_field"]
        output_path = ctx.params["output_path"]
        include_filepath = ctx.params["include_filepath"]

        view = ctx.target_view()
        total = len(view)

        export_data = []

        for i, sample in enumerate(view):
            entry = {
                "id": sample.id,
                "labels": sample[label_field].to_dict() if sample[label_field] else None
            }

            if include_filepath:
                entry["filepath"] = sample.filepath

            export_data.append(entry)

            yield ctx.trigger(
                "set_progress",
                {"progress": (i + 1) / total, "label": f"Exporting {i + 1}/{total}"}
            )

        # Write to file
        output_path = os.path.expanduser(output_path)
        with open(output_path, "w") as f:
            json.dump(export_data, f, indent=2)

        yield {
            "status": "success",
            "exported": len(export_data),
            "output_path": output_path
        }

    def resolve_output(self, ctx):
        outputs = types.Object()

        result = ctx.results or {}

        outputs.str(
            "message",
            label="Result",
            view=types.MarkdownView(),
            default=f"**Exported {result.get('exported', 0)} samples** to `{result.get('output_path', 'unknown')}`"
        )

        return types.Property(outputs)


def register(p):
    p.register(ExportLabels)
```

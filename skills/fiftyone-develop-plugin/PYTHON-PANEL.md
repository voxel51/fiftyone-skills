# Python Panel Development

## Contents
- [Scope](#scope)
- [How Panels Work](#how-panels-work)
- [Panel Anatomy](#panel-anatomy)
- [PanelConfig Options](#panelconfig-options)
- [State vs Data vs Store](#state-vs-data-vs-store)
- [State Anti-Patterns](#state-anti-patterns)
- [UI Components Reference](#ui-components-reference)
- [Event Handlers](#event-handlers)
- [Triggering Operators](#triggering-operators)
- [Using Execution Store](#using-execution-store)
- [Boundary System](#boundary-system)
- [Complete Example](#complete-example-sample-statistics-panel)

---

## Scope

**This file covers:** Python-only panels using `foo.Panel` — the render cycle, state management, event handlers, UI components, layout containers, Plotly charts, and the execution store.

**Out of scope:**
- React/TypeScript panels with custom components → see [JAVASCRIPT-PANEL.md](JAVASCRIPT-PANEL.md)
- Hybrid panels (Python backend + React frontend) → see [HYBRID-PLUGINS.md](HYBRID-PLUGINS.md)
- Non-panel operators (forms, dialogs) → see [PYTHON-OPERATOR.md](PYTHON-OPERATOR.md)

---

## How Panels Work

A panel is a **server-side state machine** rendered by the FiftyOne App on demand.

**Render cycle:**
1. User opens panel or triggers an event (click, input change, view change)
2. Python `render(ctx)` is called on the server
3. `render()` returns a JSON schema describing the UI (`types.Property(panel)`)
4. SchemaIO (client) renders MUI components from the schema
5. User interacts → another call to `render(ctx)` → repeat

**What this means in practice:**
- `render()` runs on every interaction — keep it fast; do not run dataset queries inside it
- Initialize state in `on_load()` or `on_change_*` handlers; read it in `render()` via `ctx.panel.get_state()`
- `default=` in the schema is part of the JSON sent to the client on every render. If `default=` reads from state and state changes, the schema changes, triggering another render call — causing an infinite loop. See [State Anti-Patterns](#state-anti-patterns).

**Handler binding rule (critical):**
`on_click` and `on_change` must be **bound instance methods** — `self.method_name`. The framework reads `handler.__self__` to build the handler URI at schema definition time. `@staticmethod` and bare function references have no `__self__` — they silently produce broken event wiring with no error message.

```python
# CORRECT — bound instance method
panel.btn("run", label="Run", on_click=self.on_run)

# WRONG — @staticmethod has no __self__, button silently does nothing
@staticmethod
def on_run(ctx): ...
panel.btn("run", label="Run", on_click=MyPanel.on_run)  # broken, no error
```

**Three storage mechanisms at a glance:**

| Storage | Set | Read back from Python | Survives reload |
|---------|-----|----------------------|-----------------|
| `ctx.panel.set_state("key", val)` | In any handler | Yes, `get_state("key")` | No |
| `ctx.panel.set_data("key", val)` | In any handler | No (client-side only) | No |
| `ctx.store("ns").set("key", val)` | In any handler | Yes, `store.get("key")` | Yes |

---

## Panel Anatomy

```python
import fiftyone.operators as foo
import fiftyone.operators.types as types


class MyPanel(foo.Panel):
    @property
    def config(self):
        """Panel metadata and configuration"""
        return foo.PanelConfig(
            name="my_panel",
            label="My Panel",
            surfaces="grid",  # "grid", "modal", or "grid modal"
            help_markdown="Panel help documentation"
        )

    def on_load(self, ctx):
        """Initialize panel state when opened"""
        ctx.panel.set_state("counter", 0)
        ctx.panel.set_data("plot_data", None)

    def on_unload(self, ctx):
        """Cleanup when panel is closed (optional)"""
        pass

    def on_change_ctx(self, ctx):
        """React to App context changes (optional)"""
        # Called when dataset, view, or selection changes
        pass

    def on_change_view(self, ctx):
        """React to view changes (optional)"""
        pass

    def on_change_selected(self, ctx):
        """React to selection changes (optional)"""
        pass

    def on_custom_event(self, ctx):
        """Custom event handler"""
        pass

    def render(self, ctx):
        """Define panel layout and components"""
        panel = types.Object()

        # Add UI components
        panel.str("message", default="Hello!")

        panel.btn(
            "my_button",
            label="Click Me",
            on_click=self.on_custom_event
        )

        return types.Property(panel)


def register(p):
    p.register(MyPanel)
```

## PanelConfig Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `name` | str | Required | Panel identifier (snake_case) |
| `label` | str | Required | Display name |
| `surfaces` | str | "grid" | Where panel appears: "grid", "modal", "grid modal" |
| `help_markdown` | str | "" | Help documentation for panel |
| `unlisted` | bool | False | Hide from panel list |

### Surface Types

| Surface | Description |
|---------|-------------|
| `"grid"` | Panel appears in grid space alongside samples |
| `"modal"` | Panel opens in modal dialog |
| `"grid modal"` | Panel can appear in either location |

## State vs Data vs Store

Panels have three storage mechanisms:

| Storage | Lifetime | Readable | Best For |
|---------|----------|----------|----------|
| `ctx.panel.state` | Transient (resets on reload) | Yes | UI state, form values |
| `ctx.panel.data` | Transient (resets on reload) | No | Large data (plots, tables) |
| `ctx.store()` | Persistent (survives sessions) | Yes | User configs, cached results |

### State (Lightweight)
- Included in every render cycle
- Readable and writable from Python
- Best for small values (counters, flags, selections)

```python
def on_load(self, ctx):
    ctx.panel.set_state("counter", 0)
    ctx.panel.set_state("selected_items", [])

def render(self, ctx):
    panel = types.Object()
    count = ctx.panel.get_state("counter", 0)
    panel.md(f"**Count:** {count}", name="count_display")  # display-only
    return types.Property(panel)
```

### Data (Large Content)
- Stored client-side only
- Write-only from Python (can't read back)
- Best for large data like plots

```python
def on_load(self, ctx):
    ctx.panel.set_data("my_plot", {
        "data": [{"x": [1, 2, 3], "y": [4, 5, 6], "type": "scatter"}],
        "layout": {"title": "My Plot"}
    })

def render(self, ctx):
    panel = types.Object()
    panel.view("my_plot", types.PlotlyView(data_key="my_plot"))
    return types.Property(panel)
```

---

## State Anti-Patterns

### Render loop: `default=` from state

`default=` is part of the schema emitted by `render()`. If `default=` reads from state, the schema changes after every `set_state()` call, which triggers another render, which reads updated state, which changes the schema again — an infinite loop.

```python
# WRONG — causes infinite render loop
def render(self, ctx):
    panel = types.Object()
    panel.str("name", default=ctx.panel.get_state("name", ""))  # schema changes every render
    return types.Property(panel)
```

```python
# CORRECT — use default= for static values only; display dynamic state as markdown
def render(self, ctx):
    panel = types.Object()
    panel.str("name", label="Name")  # input — static default (empty string)
    name = ctx.panel.get_state("name", "")
    if name:
        panel.md(f"**Current:** {name}", name="name_display")  # display-only, no default
    return types.Property(panel)
```

### Unconditional `on_load()` state reset

`on_load()` fires every time the panel opens — including when the user switches datasets and the panel re-opens. Resetting state unconditionally overwrites any state restored from store or set by a prior handler.

```python
# WRONG — resets every field on every panel open
def on_load(self, ctx):
    ctx.panel.set_state("threshold", 0.5)  # wipes user's last value
    ctx.panel.set_state("selected_field", None)
```

```python
# CORRECT — guard: only initialize if not already set
def on_load(self, ctx):
    if ctx.panel.get_state("threshold") is None:
        ctx.panel.set_state("threshold", 0.5)
    if ctx.panel.get_state("selected_field") is None:
        ctx.panel.set_state("selected_field", None)
```

If you use the execution store to persist config across sessions, restore it in `on_load()` before the guard check so the stored value wins over the default:

```python
def on_load(self, ctx):
    store = ctx.store(self._get_store_key(ctx))
    saved = store.get("config")
    if saved:
        ctx.panel.set_state("config", saved)
    elif ctx.panel.get_state("config") is None:
        ctx.panel.set_state("config", {"threshold": 0.5})
```

### Querying inside `render()`

`render()` is called on every interaction. A dataset query inside it runs on every keystroke and click.

```python
# WRONG — runs a database query on every render
def render(self, ctx):
    count = len(ctx.view)  # query on every render
    panel.md(f"**Samples:** {count}", name="count_display")
```

```python
# CORRECT — query in lifecycle handlers; store result in state
def on_load(self, ctx):
    ctx.panel.set_state("count", len(ctx.view))

def on_change_view(self, ctx):
    ctx.panel.set_state("count", len(ctx.view))

def render(self, ctx):
    panel = types.Object()
    count = ctx.panel.get_state("count", 0)
    panel.md(f"**Samples:** {count}", name="count_display")
    return types.Property(panel)
```

---

## UI Components Reference

### Text Display

```python
def render(self, ctx):
    panel = types.Object()

    # Inline markdown — preferred shorthand for display text
    panel.md("**Bold** and *italic* text", name="intro")

    # Markdown via str + view (verbose but equivalent)
    panel.str(
        "markdown_content",
        view=types.MarkdownView(),
        default="**Bold** and *italic* text"
    )

    # Section header
    panel.str(
        "header",
        view=types.Header(),
        default="Section Header"
    )

    return types.Property(panel)
```

### Input Components

```python
def render(self, ctx):
    panel = types.Object()

    # Text input
    panel.str(
        "text_input",
        label="Enter text",
        on_change=self.on_text_change
    )

    # Number input
    panel.int(
        "number_input",
        label="Enter number",
        default=10,
        on_change=self.on_number_change
    )

    # Checkbox
    panel.bool(
        "checkbox",
        label="Enable feature",
        default=False,
        on_change=self.on_checkbox_change
    )

    # Dropdown
    panel.enum(
        "dropdown",
        values=["option1", "option2", "option3"],
        label="Select option",
        on_change=self.on_dropdown_change
    )

    return types.Property(panel)
```

### Buttons

```python
def render(self, ctx):
    panel = types.Object()

    # Standard button
    panel.btn(
        "action_button",
        label="Run Action",
        on_click=self.on_action_click
    )

    # Button with icon
    panel.btn(
        "icon_button",
        label="Download",
        icon="download",
        on_click=self.on_download
    )

    # Disabled button
    is_ready = ctx.panel.get_state("ready", False)
    panel.btn(
        "conditional_button",
        label="Process",
        disabled=not is_ready,
        on_click=self.on_process
    )

    return types.Property(panel)
```

### Layout Containers

`h_stack`, `v_stack`, and `grid` all pass kwargs through to their underlying view class. Key kwargs for all three (via `GridView`):

| Kwarg | Values | Default | Effect |
|-------|--------|---------|--------|
| `gap` | int | 1 | Spacing between children |
| `align_x` | `"left"`, `"center"`, `"right"` | `"left"` | Horizontal alignment |
| `align_y` | `"top"`, `"center"`, `"bottom"` | `"top"` | Vertical alignment |
| `variant` | `"paper"`, `"outline"` | None | Visual container style |

```python
def render(self, ctx):
    panel = types.Object()

    # Horizontal layout — label next to a slider (realistic dense example)
    row = panel.h_stack("threshold_row", gap=2, align_y="center")
    row.md("**Threshold**", name="threshold_label")
    row.float("threshold", min=0.0, max=1.0, view=types.SliderView())

    # Vertical layout
    col = panel.v_stack("info_col", gap=1)
    col.md("**Dataset:** " + ctx.dataset.name, name="ds_name")
    col.md(f"**Samples:** {ctx.panel.get_state('count', 0)}", name="sample_count")

    # 2D grid — components flow into rows automatically
    grid = panel.grid("actions_grid", gap=2)
    grid.btn("btn_a", label="Export", icon="download", on_click=self.on_export)
    grid.btn("btn_b", label="Refresh", icon="refresh", on_click=self.on_refresh)
    grid.btn("btn_c", label="Reset", icon="undo", on_click=self.on_reset)

    return types.Property(panel)
```

### Data Visualization

**Note:** Python panels have limited visualization capabilities. For rich media display (images, videos, thumbnails), use JavaScript panels instead.

```python
def render(self, ctx):
    panel = types.Object()

    # Plotly chart (data must be set via set_data before render is called)
    panel.view("chart", types.PlotlyView(data_key="chart_data"))

    # Display file info as markdown (panel.image() does not exist)
    filepath = ctx.panel.get_state("filepath", "")
    if filepath:
        import os
        panel.md(f"**File:** `{os.path.basename(filepath)}`", name="file_info")

    return types.Property(panel)
```

### Plotly Click Events (click-to-filter)

Use `panel.plot()` instead of `panel.view()` when you need click or selection handlers. Pass `on_click` and/or `on_selected` as bound methods — they follow the same binding rule as buttons.

```python
def on_load(self, ctx):
    ctx.panel.set_data("label_dist", {
        "data": [{"x": ["car", "person", "bike"], "y": [40, 25, 15], "type": "bar",
                  "ids": ["car", "person", "bike"]}],
        "layout": {"title": "Label Distribution"}
    })

def on_bar_click(self, ctx):
    # ctx.params contains: x, y, id, trace, trace_idx, idx, shift_pressed
    label = ctx.params.get("x")
    if label:
        # Filter the view to samples containing this label
        ctx.ops.set_view(
            ctx.view.filter_labels("ground_truth", F("label") == label)
        )

def on_bar_selected(self, ctx):
    # ctx.params["data"] is a list of selected points, each with x, y, id, trace_idx, idx
    selected_labels = [p["x"] for p in ctx.params.get("data", [])]
    if selected_labels:
        ctx.ops.set_view(
            ctx.view.filter_labels("ground_truth", F("label").is_in(selected_labels))
        )

def render(self, ctx):
    panel = types.Object()
    # Use panel.plot() (not panel.view()) to attach event handlers
    panel.plot(
        "label_dist",
        on_click=self.on_bar_click,
        on_selected=self.on_bar_selected,
        data_key="label_dist"
    )
    return types.Property(panel)
```

**Click handler params available in `ctx.params`:**

| Key | Value |
|-----|-------|
| `x` | x value of the clicked point |
| `y` | y value of the clicked point |
| `id` | `data.ids[idx]` — use this to store stable IDs |
| `trace` | `data[trace_idx].name` |
| `trace_idx` | index of the trace |
| `idx` | index within the trace |
| `shift_pressed` | bool — whether Shift was held |

For `on_selected`, `ctx.params["data"]` is a list of the above dicts for each selected point.

**Note:** `ctx.ops.set_view()` takes a FiftyOne view object. Use `from fiftyone import ViewField as F` for filter expressions.

**Limitations:**
- `panel.media()`, `panel.image()`, `panel.table()` do NOT exist
- For image thumbnails or media preview, use JavaScript panels
- For tables, format data as markdown or use PlotlyView with table trace

## Event Handlers

### Built-in Events

All officially supported event handlers (source: `panel.py`):

```python
def on_load(self, ctx):
    """Called when panel opens"""
    ctx.panel.set_state("initialized", True)

def on_unload(self, ctx):
    """Called when panel closes"""
    pass

def on_change(self, ctx):
    """Called on any context change"""
    pass

def on_change_ctx(self, ctx):
    """Called when App context changes (dataset, view, selection)"""
    ctx.panel.set_state("dataset_name", ctx.dataset.name)

def on_change_dataset(self, ctx):
    """Called when the active dataset changes"""
    pass

def on_change_view(self, ctx):
    """Called when view changes"""
    ctx.panel.set_state("view_count", len(ctx.view))

def on_change_selected(self, ctx):
    """Called when sample selection changes"""
    ctx.panel.set_state("selected_count", len(ctx.selected))

def on_change_selected_labels(self, ctx):
    """Called when label selection changes"""
    pass

def on_change_current_sample(self, ctx):
    """Called when the current sample in modal changes"""
    pass

def on_change_spaces(self, ctx):
    """Called when panel layout spaces change"""
    pass
```

> **Note:** The handler is `on_change_selected`, not `on_change_selection`.

### Custom Events

```python
def on_button_click(self, ctx):
    """Custom click handler"""
    count = ctx.panel.get_state("counter", 0)
    ctx.panel.set_state("counter", count + 1)

def on_input_change(self, ctx):
    """Custom change handler"""
    value = ctx.params.get("value")
    ctx.panel.set_state("input_value", value)

def on_select_sample(self, ctx):
    """Handle sample selection"""
    sample_id = ctx.params.get("sample_id")
    if sample_id:
        ctx.ops.set_selected_samples([sample_id])
```

## Triggering Operators

Panels can trigger operators:

```python
def on_run_operator(self, ctx):
    """Trigger an operator from panel"""
    ctx.trigger(
        "@voxel51/brain/compute_similarity",
        params={
            "brain_key": "my_similarity",
            "model": "clip-vit-base32-torch"
        }
    )
```

## Using Execution Store

Store data beyond panel lifetime with namespaced keys:

```python
class MyPanel(foo.Panel):
    version = "v1"

    def _get_store_key(self):
        # ctx.store() scopes by dataset_id automatically — just use a plugin-unique name
        plugin_name = self.config.name.split("/")[-1]
        return f"{plugin_name}_v{self.version}"

    def on_load(self, ctx):
        store = ctx.store(self._get_store_key())

        saved_config = store.get("user_config")
        if saved_config:
            ctx.panel.set_state("config", saved_config)
        else:
            ctx.panel.set_state("config", {"default": True})

    def on_save_config(self, ctx):
        store = ctx.store(self._get_store_key())
        store.set("user_config", ctx.panel.get_state("config"))

    def on_change_dataset(self, ctx):
        # Reinitialize when dataset changes (store is scoped per dataset by the framework)
        self.on_load(ctx)
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
```

See [EXECUTION-STORE.md](EXECUTION-STORE.md) for advanced caching patterns.

---

## Boundary System

| Action | Rule |
|--------|------|
| Reading dataset schema, listing fields, reading state | **Free** — safe reads |
| Calling `ctx.panel.set_state()` / `set_data()` / `ctx.store().set()` | **Free** — standard panel operations |
| Running `len(ctx.view)` or other queries | **Free in handlers** — never inside `render()` |
| Tagging samples, adding fields, modifying label values | **Confirm first** — data mutation |
| `fo.delete_dataset()`, dropping indexes, overwriting labels without backup | **Never from a panel** |
| Running dataset queries inside `render()` | **Never** — runs on every interaction |

**Safe testing directive:** Clone the target dataset before testing mutations: `dataset.clone()`.

---

## Complete Example: Sample Statistics Panel

Demonstrates: lifecycle hooks, state management, layout containers, Plotly chart, field selector, `register(p)`.

All files needed to run this plugin:

**fiftyone.yml**
```yaml
name: "@myorg/sample-statistics"
version: "1.0.0"
description: "Panel showing label distribution for the current view"
fiftyone:
  version: ">=0.23"
panels:
  - statistics_panel
```

**Directory layout:**
```
~/.fiftyone/plugins/
└── myorg_sample_statistics/
    ├── fiftyone.yml
    └── __init__.py
```

**__init__.py**
```python
import fiftyone.operators as foo
import fiftyone.operators.types as types


class StatisticsPanel(foo.Panel):
    @property
    def config(self):
        return foo.PanelConfig(
            name="statistics_panel",
            label="Sample Statistics",
            surfaces="grid",
            help_markdown="View dataset statistics"
        )

    def on_load(self, ctx):
        self._update_stats(ctx)

    def on_change_view(self, ctx):
        self._update_stats(ctx)

    def _update_stats(self, ctx):
        view = ctx.view
        total_samples = len(view)
        ctx.panel.set_state("total_samples", total_samples)

        label_counts = {}
        schema = ctx.dataset.get_field_schema()

        for field_name, field in schema.items():
            if hasattr(field, "document_type"):
                if "Detection" in str(field.document_type):
                    counts = view.count_values(f"{field_name}.detections.label")
                    label_counts[field_name] = dict(counts)

        ctx.panel.set_state("label_counts", label_counts)

        if label_counts:
            first_field = list(label_counts.keys())[0]
            self._set_plot(ctx, first_field, label_counts[first_field])

    def _set_plot(self, ctx, field_name, counts):
        ctx.panel.set_data("label_plot", {
            "data": [{
                "x": list(counts.keys()),
                "y": list(counts.values()),
                "type": "bar"
            }],
            "layout": {
                "title": f"Label Distribution ({field_name})",
                "xaxis": {"title": "Label"},
                "yaxis": {"title": "Count"}
            }
        })

    def on_refresh(self, ctx):
        self._update_stats(ctx)

    def on_field_change(self, ctx):
        selected_field = ctx.params.get("value")
        label_counts = ctx.panel.get_state("label_counts", {})
        if selected_field in label_counts:
            self._set_plot(ctx, selected_field, label_counts[selected_field])

    def render(self, ctx):
        panel = types.Object()

        # Header row: title + refresh button side by side
        header_row = panel.h_stack("header_row", align_y="center", gap=2)
        header_row.str("title", view=types.Header(), default="Dataset Statistics")
        header_row.btn("refresh_btn", label="Refresh", icon="refresh",
                       on_click=self.on_refresh)

        # Stats row
        total = ctx.panel.get_state("total_samples", 0)
        panel.md(f"**Total Samples:** {total}", name="count_display")

        # Field selector + plot
        label_counts = ctx.panel.get_state("label_counts", {})
        if label_counts:
            panel.enum(
                "field_selector",
                values=list(label_counts.keys()),
                label="Label Field",
                on_change=self.on_field_change
            )
            panel.view("label_plot", types.PlotlyView(data_key="label_plot"))
        else:
            panel.md("*No detection fields found in this dataset.*",
                     name="no_data_msg")

        return types.Property(panel)


def register(p):
    p.register(StatisticsPanel)
```

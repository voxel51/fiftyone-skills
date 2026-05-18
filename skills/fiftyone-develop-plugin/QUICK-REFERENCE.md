# Quick Reference

Lookup tables and a minimal working example. Read this when you need to check a type, option name, or want a copy-pasteable starting point.

---

## Plugin Types

| Type | Language | Use Case |
|------|----------|----------|
| Operator | Python | Data processing, computations, form-based actions |
| Panel | Python-only (default) | Persistent UI — prefer this unless rich React components are needed |
| Panel | Hybrid | Python backend + React frontend — only when Python UI is insufficient |

---

## Operator Config Options

| Option | Default | Effect |
|--------|---------|--------|
| `dynamic` | False | Recalculate inputs on change (runs `resolve_input` on every keystroke — keep it fast) |
| `execute_as_generator` | False | Stream progress updates with `yield` |
| `allow_immediate_execution` | True | Execute in foreground |
| `allow_delegated_execution` | False | Allow background execution |
| `default_choice_to_delegated` | False | Default to background when both modes are allowed |
| `unlisted` | False | Hide from operator browser |
| `on_startup` | False | Execute when App starts |
| `on_dataset_open` | False | Execute when a dataset is opened |

---

## Panel Config Options

| Option | Default | Effect |
|--------|---------|--------|
| `surfaces` | `"grid"` | Where panel can display: `"grid"`, `"modal"`, `"grid modal"` |
| `allow_multiple` | False | Allow multiple instances of the panel |
| `category` | None | Panel category in browser |
| `priority` | None | Sort order in UI |
| `unlisted` | False | Hide from panel browser |

---

## Input Types (Operators)

| Type | Method | Notes |
|------|--------|-------|
| Text | `inputs.str()` | |
| Integer | `inputs.int(min=..., max=...)` | |
| Float | `inputs.float(min=..., max=...)` | |
| Boolean | `inputs.bool()` | Renders as checkbox |
| Dropdown | `inputs.enum(values=[...])` | |
| Radio buttons | `inputs.enum(values=[...], view=types.RadioGroup())` | |
| File selector | `inputs.file()` | |
| File upload | `inputs.uploaded_file()` | Content included in `ctx.params` |
| View target | `inputs.view_target(ctx)` | Dataset / current view / selected samples selector |
| Nested object | `inputs.obj(name)` | Returns sub-Object; access as `ctx.params["name"]` dict |
| List | `inputs.list(name, element_type)` | e.g., `inputs.list("tags", types.String())` |
| Key-value map | `inputs.map(name, key_type, value_type)` | |
| Directory path | `inputs.str(name, view=types.DirectoryView())` | |

---

## Panel UI Components

All methods live on the `types.Object()` returned from `render()`. Use `h_stack`/`v_stack`/`grid` — agents default to vertical stacking, which produces poor layouts.

| Component | Method | Notes |
|-----------|--------|-------|
| Text input | `panel.str()` | |
| Number input | `panel.int()` / `panel.float(min=..., max=...)` | |
| Checkbox | `panel.bool()` | |
| Dropdown | `panel.enum(values=[...])` | |
| Button | `panel.btn(label=..., on_click=self.handler)` | handler must be bound instance method |
| Markdown display | `panel.md("**text**")` | shorthand; use for display-only labels |
| Plotly chart (display) | `panel.view("key", types.PlotlyView(data_key="key"))` | data set via `ctx.panel.set_data()` |
| Plotly chart (interactive) | `panel.plot("key", on_click=self.handler, data_key="key")` | use when you need click/select events |
| Horizontal row | `panel.h_stack("row")` → sub-Object | children laid out left→right |
| Vertical column | `panel.v_stack("col")` → sub-Object | children laid out top→bottom |
| 2D grid | `panel.grid("g")` → sub-Object | use `gap`, `align_x`, `align_y` kwargs |

**Dense layout example** (slider next to label — the pattern agents get wrong most often):

```python
def render(self, ctx):
    panel = types.Object()
    row = panel.h_stack("threshold_row")
    row.md("**Threshold**", name="threshold_label")   # md() for display-only label
    row.float("threshold", min=0.0, max=1.0, view=types.SliderView())
    return types.Property(panel)
```

> **`LabelValueView` restriction:** Read-only display of existing values only — unsupported on input properties like `str()` or `float()`. Use `panel.md()` for inline labels next to inputs instead.

See [PYTHON-PANEL.md](PYTHON-PANEL.md#layout-containers) for full layout reference including GridView kwargs.

---

## Minimal Working Example

The smallest complete plugin. Use this as a copy-paste starting point.

**Directory layout:**
```
~/.fiftyone/plugins/
└── myorg_hello_world/          ← directory name: underscores, no @ or -
    ├── fiftyone.yml
    └── __init__.py
```

**fiftyone.yml:**
```yaml
name: "@myorg/hello-world"
version: "1.0.0"
description: "Hello world operator"
fiftyone:
  version: ">=0.23"
operators:
  - hello_world
```

> **URI vs directory name:** The `@myorg/hello-world` URI lives only inside `fiftyone.yml`. The directory just needs to contain that file — its name doesn't need to match. `_to_python_safe_name()` derives the module name from the YAML `name:` field, not the directory.

**__init__.py:**
```python
import fiftyone.operators as foo
import fiftyone.operators.types as types


class HelloWorld(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="hello_world",
            label="Hello World"
        )

    def resolve_input(self, ctx):
        inputs = types.Object()
        inputs.str("message", label="Message", default="Hello!")
        return types.Property(inputs)

    def execute(self, ctx):
        print(ctx.params["message"])
        return {"status": "done"}


def register(p):
    p.register(HelloWorld)
```

**Install and test:**
```bash
PLUGINS_DIR=$(python -c "import fiftyone as fo; print(fo.config.plugins_dir)")
ln -s /path/to/myorg_hello_world "$PLUGINS_DIR/myorg_hello_world"
fiftyone app debug
# Open operator browser → search "Hello World"
```

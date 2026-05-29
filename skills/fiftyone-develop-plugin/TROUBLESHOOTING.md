# Troubleshooting FiftyOne Plugins

## Contents
- [Pre-Flight Check](#pre-flight-check)
- [One-Shot Plugin Diagnostic](#one-shot-plugin-diagnostic)
- [Reload vs Restart](#reload-vs-restart)
- [App Lifecycle](#app-lifecycle)
- [Top Errors with Exact Fixes](#top-errors-with-exact-fixes)
- [State and Panel Debugging](#state-and-panel-debugging)
- [Operator Debugging](#operator-debugging)

---

## Pre-Flight Check

Run these before debugging anything else. Many sessions stall because one of these is false.

```bash
# 1. Is the App running?
curl -s http://localhost:5151/operators > /dev/null && echo "App is UP" || echo "App is DOWN — run: python -c \"import fiftyone as fo; fo.launch_app()\""

# 2. Does your plugins directory exist and contain your plugin?
python3 -c "import fiftyone as fo; print(fo.config.plugins_dir)"
ls $(python3 -c "import fiftyone as fo; print(fo.config.plugins_dir)")

# 3. Does your plugin directory have a fiftyone.yml?
ls $(python3 -c "import fiftyone as fo; print(fo.config.plugins_dir)")/YOUR_PLUGIN_DIR/fiftyone.yml
```

**MCP pre-flight:** If Claude is using MCP tools to interact with the App, verify MCP is active by running `fiftyone__list_plugins` or `fiftyone__get_context_info`. If MCP tools return errors, the App session needs to be started in the same Python environment where FiftyOne is installed — MCP does not work across virtual environments.

---

## One-Shot Plugin Diagnostic

Run this whenever a plugin isn't loading or operators aren't appearing. It returns all Python-level load errors from the plugin registry.

```bash
curl -s -X POST http://localhost:5151/operators \
  -H 'Content-Type: application/json' -d '{}' \
  | python3 -c "
import json, sys
d = json.load(sys.stdin)
errors = d.get('errors', [])
if errors:
    print('PLUGIN LOAD ERRORS:')
    for e in errors: print(' -', e)
else:
    ops = d.get('operators', [])
    print(f'No load errors. {len(ops)} operators registered.')
    for op in ops: print(f'  {op.get(\"name\", \"?\")}')
"
```

**What the output means:**

| Output | Meaning |
|--------|---------|
| `No load errors. 0 operators registered` | `register(p)` is missing or empty — see Error #2 below |
| `No load errors. N operators registered` | Plugin loaded. If panel still doesn't show, restart the App |
| `SyntaxError: ...` | Python syntax error in `__init__.py` — fix it, browser-refresh |
| `ModuleNotFoundError: ...` | Import failure — check your imports, check `requirements.txt` |
| `AttributeError: ...` | Likely a mis-named method or wrong API call |
| Connection refused | App is not running |

---

## Reload vs Restart

The wrong action wastes many prompts. Use this table.

| Change type | What to do |
|-------------|------------|
| Python logic change in `execute()` or a handler | Browser hard-refresh (Cmd+Shift+R / Ctrl+Shift+F5) |
| New operator or panel added to `fiftyone.yml` | **Full App restart** + browser refresh |
| New operator or panel class added to `__init__.py` | **Full App restart** + browser refresh |
| JavaScript bundle rebuilt (`npm run build`) | **Full App restart** + browser hard-refresh |
| `fiftyone.yml` name or version changed | **Full App restart** |
| Dataset reload (`reload_dataset`) | Only needed when dataset documents change outside Python |

**Full App restart:**
```python
# Stop the running session, then:
import fiftyone as fo
session = fo.launch_app(dataset)
```

**Why browser hard-refresh matters for JS:** The App caches the JS bundle. A normal refresh may serve the old bundle even after a restart.

---

## App Lifecycle

### Keeping the App alive from a script

```python
import fiftyone as fo

dataset = fo.load_dataset("my-dataset")
session = fo.launch_app(dataset)
session.wait()  # blocks until the App window is closed — use in standalone scripts
```

### Safe testing: always clone your dataset

Work on a clone during development to avoid corrupting real data:

```python
import fiftyone as fo

src = fo.load_dataset("my-real-dataset")
test_ds = src.clone("my-real-dataset-dev")  # safe copy
# develop against test_ds; delete when done
fo.delete_dataset("my-real-dataset-dev")
```

### Debug logging

```python
def execute(self, ctx):
    print(f"Params: {ctx.params}")
    print(f"View stages: {ctx.view.stages}")
    print(f"Selected: {ctx.selected}")
```

Python `print()` output goes to the terminal running the server. Start the server separately to see it:

```bash
python -m fiftyone.server.main   # Terminal 1 — logs appear here
fiftyone app debug               # Terminal 2 — or launch with dataset
```

---

## Top Errors with Exact Fixes

### Error 1: Panel/operator appears in the list but doesn't work

**Symptom:** Operator is visible in the browser, but clicking it does nothing, or panel opens blank.

**Diagnostic:**
```bash
# Check for load errors first
curl -s -X POST http://localhost:5151/operators \
  -H 'Content-Type: application/json' -d '{}' | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('errors', 'none'))"
```

**Causes and fixes:**
- Python syntax error in `__init__.py` → fix the syntax, browser-refresh (no restart needed)
- `render()` raises an uncaught exception → check server terminal for the traceback
- Handler method missing or misspelled → check method name (e.g., `on_change_selected` not `on_change_selection`)

---

### Error 2: Plugin loads but zero operators are registered

**Symptom:** `/operators` returns `"No load errors. 0 operators registered."` The plugin is enabled in the App.

**Root cause:** `register(p)` function is missing, empty, or raises silently.

```python
# WRONG — plugin loads, no error, but ZERO operators appear in the App
def register(p):
    pass  # forgot p.register(MyPanel)

# WRONG — register raises silently (e.g. wrong class passed)
def register(p):
    p.register(MyPanel())  # passing an instance instead of the class — silent error

# CORRECT
def register(p):
    p.register(MyPanel)
    p.register(MyOperator)
```

**Fix:** Add or correct `register(p)` at the bottom of `__init__.py`, then browser-refresh (no restart needed for this change).

---

### Error 3: Panel renders once then freezes or keeps re-rendering

**Symptom:** Panel loads once, then interactions produce no response. Or the panel continuously re-renders (spinner loops).

**Root cause A — infinite render loop:** `default=` reads from `ctx.panel.get_state()`. Schema changes each render → re-render → schema changes → infinite loop.

```python
# WRONG — causes infinite render loop
panel.str("name", default=ctx.panel.get_state("name", ""))

# CORRECT — use default= for static values only; display state as markdown
panel.str("name", label="Name")           # input, static default
name = ctx.panel.get_state("name", "")
if name:
    panel.md(f"**Current:** {name}", name="name_display")
```

**Root cause B — button handler is a static method or unbound function:**

```python
# WRONG — @staticmethod has no __self__, button silently does nothing
@staticmethod
def on_click(ctx): ...
panel.btn("run", label="Run", on_click=MyPanel.on_click)

# CORRECT
def on_click(self, ctx): ...
panel.btn("run", label="Run", on_click=self.on_click)
```

---

### Error 4: `on_change_*` handler never fires

**Symptom:** You define an `on_change_*` method but it is never called when the expected event occurs.

**Cause:** The method name does not match any registered hook. Common misspellings:

| Wrong | Correct |
|-------|---------|
| `on_change_selection` | `on_change_selected` |
| `on_change_sample` | `on_change_current_sample` |
| `on_change_labels` | `on_change_selected_labels` |

**Complete list of valid hook names** (from `panel.py`): `on_load`, `on_unload`, `on_change`, `on_change_ctx`, `on_change_dataset`, `on_change_view`, `on_change_spaces`, `on_change_current_sample`, `on_change_selected`, `on_change_selected_labels`, `on_change_extended_selection`, `on_change_group_slice`, `on_change_query_performance`, `on_change_active_fields`.

---

### Error 5: `ctx.current_sample` causes AttributeError

**Symptom:** `AttributeError: 'str' object has no attribute 'filepath'` (or similar) when accessing sample data.

**Root cause:** `ctx.current_sample` is a **string ID**, not a `Sample` object.

```python
# WRONG
filepath = ctx.current_sample.filepath  # AttributeError

# CORRECT
sample_id = ctx.current_sample           # string ID
sample = ctx.dataset[sample_id]          # fetch the Sample
filepath = sample.filepath
```

---

## State and Panel Debugging

### Print state contents

```python
def on_load(self, ctx):
    # Print current state to server terminal (panel_state is readable)
    print(f"=== PANEL STATE: {ctx.panel_state} ===")
    # Note: panel data is write-only (client-side) — cannot be read back from Python
```

### Verify store contents

```python
def on_load(self, ctx):
    store = ctx.store("my_store")
    print(f"Store keys: {store.list_keys()}")
    for key in store.list_keys():
        print(f"  {key}: {store.get(key)}")
```

### Isolate render issues

If a panel produces no visible output, add this minimal render to confirm the framework is working, then add components back one by one:

```python
def render(self, ctx):
    panel = types.Object()
    panel.md("**Panel is rendering**", name="debug")
    return types.Property(panel)
```

### Check server logs

Always run the FiftyOne server in a terminal where you can see Python output:

```bash
# Terminal 1: server with visible logs
python -m fiftyone.server.main

# Terminal 2: launch app (connect to running server)
python3 -c "import fiftyone as fo; fo.launch_app()"
```

Python exceptions from `render()`, `execute()`, and event handlers print to the server terminal. Without this, errors are invisible.

---

## Operator Debugging

### Inspect what the operator received

```python
def execute(self, ctx):
    print(f"=== {self.config.name} ===")
    print(f"params: {ctx.params}")
    print(f"dataset: {ctx.dataset.name}")
    print(f"view stages: {ctx.view.stages}")
    print(f"selected: {ctx.selected}")
    target = ctx.target_view()
    print(f"target count: {len(target)}")
```

### Operator not showing in browser

1. Run the one-shot diagnostic — check `errors` key
2. Verify the operator name in `fiftyone.yml` matches the `name` field in `OperatorConfig`
3. Restart the App if you added a new operator after the last restart
4. Check `unlisted=True` is not accidentally set in `OperatorConfig`

### Generator operator hangs

If `execute_as_generator=True` and the operator appears to hang with no progress:

```python
# Every yield must be a trigger or a dict — not None
yield ctx.trigger("set_progress", {"progress": 0.5, "label": "..."})  # OK
yield {"status": "done"}   # OK at the end
# yield None               # WRONG — breaks the generator
```

### Delegated operator not running

```python
# Check if delegation is configured correctly
@property
def config(self):
    return foo.OperatorConfig(
        name="my_op",
        allow_delegated_execution=True,
        allow_immediate_execution=True,  # both flags needed for user choice
    )

# Check that a delegated executor is running
# fiftyone delegated launch  (in a separate terminal)
```

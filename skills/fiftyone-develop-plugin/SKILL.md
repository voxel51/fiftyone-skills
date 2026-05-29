---
name: fiftyone-develop-plugin
description: Develops custom FiftyOne plugins (operators and panels) from scratch. Use when creating plugins, extending FiftyOne with custom operators, building interactive panels, or integrating external APIs.
---

# Develop FiftyOne Plugins

## TL;DR — Read This First

**Step 1: Decide what you're building.**

| Goal | Type | Read next |
|------|------|-----------|
| Run a computation, process samples, trigger actions | **Operator** | [PYTHON-OPERATOR.md](PYTHON-OPERATOR.md) |
| Persistent panel in the grid, simple/form UI | **Python Panel** | [PYTHON-PANEL.md](PYTHON-PANEL.md) |
| Persistent panel in the grid, rich/interactive UI | **Hybrid Panel** | [HYBRID-PLUGINS.md](HYBRID-PLUGINS.md) + [JAVASCRIPT-PANEL.md](JAVASCRIPT-PANEL.md) |
| Panel that opens inside the sample modal | **JS Modal Panel** | [JAVASCRIPT-PANEL.md](JAVASCRIPT-PANEL.md) |

**Step 2: Read that file NOW — before generating any code.** Each file contains patterns that are not in SKILL.md. Missing them causes the most common failures (wrong `default=` usage, handler binding errors, panel not appearing in App).

**If something isn't rendering or you hit an error:** Read [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for the one-shot diagnostic command, reload vs restart table, and the top 5 error patterns with exact fixes.

**For input types, Panel UI components reference, and a minimal working example:** Read [QUICK-REFERENCE.md](QUICK-REFERENCE.md).

**Step 3: Clone the official plugins repo for reference patterns:**
```bash
git clone https://github.com/voxel51/fiftyone-plugins.git /tmp/fiftyone-plugins 2>/dev/null || true
```

**Step 4: Install your plugin by placing it (or symlinking it) in the plugins directory:**
```bash
PLUGINS_DIR=$(python -c "import fiftyone as fo; print(fo.config.plugins_dir)")
# Convention: use underscores in the directory name (e.g. myorg_my_plugin) for shell compatibility
# The @org/name URI lives only inside fiftyone.yml — the directory name doesn't need to match
ln -s /path/to/my_plugin "$PLUGINS_DIR/my_plugin"
```

**Step 5: Launch in debug mode so you see all server logs:**
```bash
fiftyone app debug <dataset-name>
```

---

## Key Directives

**ALWAYS follow these rules:**

### 1. Understand before coding
Ask clarifying questions. Never assume what the plugin should do.

### 2. Plan before implementing
Present file structure and design. Get user approval before generating code.

### 3. Search existing plugins for patterns
```bash
# Clone official plugins for reference
git clone https://github.com/voxel51/fiftyone-plugins.git /tmp/fiftyone-plugins 2>/dev/null || true

# Search for similar patterns
grep -r "keyword" /tmp/fiftyone-plugins/plugins/ --include="*.py" -l
```

```python
list_plugins(enabled=True)
list_operators(builtin_only=False)
get_operator_schema(operator_uri="@voxel51/brain/compute_similarity")
```

### 4. Test locally before done

```bash
# Get plugins directory
PLUGINS_DIR=$(python -c "import fiftyone as fo; print(fo.config.plugins_dir)")

# Develop plugin in plugins directory
cd $PLUGINS_DIR/my-plugin
```

Write tests:
- **Python**: `pytest` for operators/panels
- **JavaScript**: `vitest` for React components

Verify in FiftyOne App before done.

### 5. Test complex logic outside the plugin first

If the plugin wraps non-trivial processing (model inference, image transforms, external APIs), verify that logic works as standalone Python before integrating it into the plugin:

```python
# Test independently first
result = my_processing_fn(sample_path)
print(result)  # confirm correctness

# Only then wrap in execute()
def execute(self, ctx):
    result = my_processing_fn(ctx.dataset.first().filepath)
    ...
```

This prevents debugging two systems (plugin framework + custom logic) at once.

### 6. Iterate on feedback

Run server separately to see logs:
```bash
# Terminal 1: Python logs
python -m fiftyone.server.main

# Terminal 2: Browser at localhost:5151 (JS logs in DevTools console)
```

```bash
fiftyone app debug          # logs printed to shell; use with a dataset:
fiftyone app debug <dataset-name>
```

For automated iteration, use Playwright e2e tests:
```bash
npx playwright test
```

Refine until the plugin works as expected.

## Critical Patterns

### Gotcha 1 — `default=` must never reference state (causes infinite render loops)

```python
# WRONG — triggers a render loop: schema changes → re-render → schema changes → ...
def render(self, ctx):
    panel = types.Object()
    panel.str("threshold", default=ctx.panel.get_state("threshold"))  # ← NEVER do this

# CORRECT — pass a literal; read state separately for display logic
def render(self, ctx):
    panel = types.Object()
    panel.str("threshold", default="0.5")  # literal only
    current = ctx.panel.get_state("threshold", "0.5")  # read separately if needed
```

The `default=` value is part of the schema the frontend uses to decide whether to re-render. If it changes between renders (because state changed), the frontend re-dispatches, which re-renders, infinitely.

### Gotcha 2 — Event handlers must be bound instance methods, not static methods

```python
# WRONG — @staticmethod strips __self__, breaking the handler URI silently
@staticmethod
def on_click(ctx):
    ...

panel.btn("btn", label="Go", on_click=MyPanel.on_click)  # ← broken

# CORRECT — regular instance method
def on_click(self, ctx):
    ...

panel.btn("btn", label="Go", on_click=self.on_click)  # ← works
```

The framework reads `handler.__self__.uri` to build the operator-trigger URI. A `@staticmethod` has no `__self__`, so the wiring silently fails and button clicks do nothing.

### Gotcha 3 — Missing `register(p)` is a silent failure

```python
# WRONG — plugin loads, no error, but ZERO operators appear in the App
import fiftyone.operators as foo

class MyPanel(foo.Panel):
    ...

# forgot register() entirely — or it raises an exception silently
```

```python
# CORRECT — must explicitly register every operator and panel
def register(p):
    p.register(MyPanel)
    p.register(MyOperator)  # each class must be listed
```

The plugin loader calls `module.register(self)` after importing `__init__.py`. If the function is missing, raises an exception, or simply doesn't call `p.register(YourClass)` for a class, that class is never inserted into the operator registry. The App shows the plugin as **enabled** in `list_plugins()` — no error, no warning — but the operator or panel is completely invisible. This is the most common cause of "my panel doesn't appear in the + New panel menu."

**Convention on directory naming:** Use `myorg_my_plugin` (underscores, no `@` or `-`) for clarity and shell compatibility. This is convention, not a hard requirement — the loader derives the module name from `fiftyone.yml`'s `name:` field and sanitizes it automatically. The `@org/name` URI belongs in `fiftyone.yml`; the directory just needs to contain that file.

### Operator Execution
```python
# Chain operators (non-delegated operators only, in execute() only, fire-and-forget)
ctx.trigger("@plugin/other_operator", params={...})

# UI operations
ctx.ops.notify("Done!")
ctx.ops.set_progress(progress=0.5)  # keyword required — first positional arg is label, not progress
```

### View Selection
```python
# Use ctx.target_view() to respect user's current selection and filters
view = ctx.target_view()

# ctx.dataset - Full dataset (use when explicitly exporting all)
# ctx.view - Filtered view (use for read-only operations)
# ctx.target_view() - Filtered + selected samples (use for exports/processing)
```

### Store Keys (Avoid Collisions)
```python
# ctx.store() already scopes by dataset_id internally — no need to embed dataset name.
# Use a plugin-unique name to avoid collisions with other plugins on the same dataset.
def _get_store_key(self):
    return self.config.name.split("/")[-1]  # e.g. "my_panel"

store = ctx.store(self._get_store_key())
```

### Panel State vs Execution Store
```python
# ctx.panel.state - Transient (resets when panel reloads)
# ctx.store() - Persistent (survives across sessions)

def on_load(self, ctx):
    ctx.panel.state.selected_tab = "overview"  # Transient
    store = ctx.store(self._get_store_key())
    ctx.panel.state.config = store.get("user_config") or {}  # Persistent
```

### Delegated Execution
Use for operations that: process >100 samples or take >1 second.

```python
@property
def config(self):
    return foo.OperatorConfig(
        name="heavy_operator",
        allow_delegated_execution=True,
        default_choice_to_delegated=True,
    )
```

### Progress Reporting
```python
@property
def config(self):
    return foo.OperatorConfig(
        name="progress_operator",
        execute_as_generator=True,
    )

def execute(self, ctx):
    total = len(ctx.target_view())
    for i, sample in enumerate(ctx.target_view()):
        # Process sample...
        yield ctx.trigger("set_progress", {"progress": (i+1)/total})
    yield {"status": "complete"}
```

### Custom Runs (Auditability)
Use Custom Runs for operations needing reproducibility and history tracking:

```python
# Create run key (must be valid Python identifier - use underscores, not slashes)
run_key = f"my_plugin_{self.config.name}_v1_{timestamp}"

# Initialize and register
run_config = ctx.dataset.init_run(operator=self.config.name, params=ctx.params)
ctx.dataset.register_run(run_key, run_config)
```

See [PYTHON-OPERATOR.md](PYTHON-OPERATOR.md#custom-runs-auditable-operations) for full Custom Runs pattern.
See [EXECUTION-STORE.md](EXECUTION-STORE.md) for advanced caching patterns.
See [HYBRID-PLUGINS.md](HYBRID-PLUGINS.md) for Python + JavaScript communication.

## Workflow

### Phase 1: Requirements

Understand what the user needs to accomplish:

1. "What problem are you trying to solve?"
2. "What should the user be able to do?" (user's perspective)
3. "What information does the user provide?"
4. "What result does the user expect to see?"
5. "Any external data sources or services involved?"
6. "How will this fit into the user's workflow?"

### Phase 2: Design

1. Search existing plugins for similar patterns
2. **Choose the right panel architecture:**
   - **Modal panel** (appears in sample modal) → Use **JS Panel + Python Operators**. See [JAVASCRIPT-PANEL.md — Modal Panels](JAVASCRIPT-PANEL.md#modal-panels). Do NOT use `composite_view=True` — it produces "Unsupported View" errors for modal panels.
   - **Grid panel with rich UI** → Use **hybrid** (Python + JavaScript). See [HYBRID-PLUGINS.md](HYBRID-PLUGINS.md).
   - **Grid panel with simple UI** → Use **Python-only**. See [PYTHON-PANEL.md](PYTHON-PANEL.md).
3. Create plan with:
   - Plugin name (`@org/plugin-name`)
   - File structure
   - Operator/panel specs
   - Input/output definitions
3. **Get user approval before coding**

See [PLUGIN-STRUCTURE.md](PLUGIN-STRUCTURE.md) for file formats.

### Phase 3: Generate Code

**Before writing any code, read the reference file for your plugin type:**

| Building… | Read this file first |
|-----------|---------------------|
| Operator | **[PYTHON-OPERATOR.md](PYTHON-OPERATOR.md)** — input types, execution patterns, placement |
| Python panel | **[PYTHON-PANEL.md](PYTHON-PANEL.md)** — layout containers, state/data/store, event lifecycle |
| JS/hybrid panel | **[JAVASCRIPT-PANEL.md](JAVASCRIPT-PANEL.md)** + **[HYBRID-PLUGINS.md](HYBRID-PLUGINS.md)** — React components, Python↔JS bridge |
| Persistent storage | **[EXECUTION-STORE.md](EXECUTION-STORE.md)** — TTL caching, cross-session state |
| Something not rendering / errors | **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** — one-shot diagnostic, top 5 errors, reload vs restart |
| Input types, Panel UI components, minimal example | **[QUICK-REFERENCE.md](QUICK-REFERENCE.md)** — lookup tables and copy-paste starting point |

Create these files:

| File | Required | Purpose |
|------|----------|---------|
| `fiftyone.yml` | Yes | Plugin manifest |
| `__init__.py` | Yes | Python operators/panels |
| `requirements.txt` | If deps | Python dependencies |
| `package.json` | JS only | Node.js metadata |
| `src/index.tsx` | JS only | React components |

**For JavaScript panels with rich UI**: Invoke the `fiftyone-voodo-design` skill for VOODO components (buttons, inputs, toasts, design tokens). VOODO is FiftyOne's official React component library.

### Phase 4: Validate & Test

#### 4.1 Validate Detection
```python
list_plugins(enabled=True)  # Should show your plugin
list_operators()  # Should show your operators
```

**If not found:** Check fiftyone.yml syntax, Python syntax errors, restart App.

#### 4.2 Validate Schema
```python
get_operator_schema(operator_uri="@myorg/my-operator")
```

Verify inputs/outputs match your expectations.

#### 4.3 Test Execution
```python
set_context(dataset_name="test-dataset")
launch_app()
execute_operator(operator_uri="@myorg/my-operator", params={...})
```

**Common failures:**
- "Operator not found" → Check fiftyone.yml operators list
- "Missing parameter" → Check resolve_input() required fields
- "Execution error" → Check execute() implementation

### Phase 5: Iterate

1. Get user feedback
2. Fix issues (sync source and plugins directory if separate)
3. Restart App if needed
4. Repeat until working

## Quick Reference

For the full input types table, Panel UI components, config option tables, and a minimal working example:

**→ Read [QUICK-REFERENCE.md](QUICK-REFERENCE.md) now.**

## Troubleshooting

### One-shot plugin load diagnostic

Run this first whenever a plugin or operator is missing from the App:

```bash
curl -s -X POST http://localhost:5151/operators \
  -H 'Content-Type: application/json' -d '{}' \
  | python -c "
import json, sys
d = json.load(sys.stdin)
errors = d.get('errors', [])
if errors:
    print('PLUGIN LOAD ERRORS:')
    for e in errors: print(' -', e)
else:
    print('No load errors. Operators found:', len(d.get('operators', [])))
"
```

This returns every error the plugin loader captured — Python syntax errors, import failures, missing `register()` calls — in one shot. Check this before debugging anything else.

**Plugin not appearing:**
- Check `fiftyone.yml` exists in plugin root
- Verify location: `~/.fiftyone/plugins/`
- Check `register(p)` is present and calls `p.register()` for each class — see Gotcha 3 above
- Check for Python syntax errors (run the diagnostic above)
- Restart FiftyOne App

**Panel not appearing in the "+ New panel" menu:**
- Plugin must load cleanly (check diagnostic above)
- `PanelConfig.name` must match the entry under `panels:` in `fiftyone.yml`
- Restart App after adding a new panel — the panel registry is built at startup

**Operator not found:**
- Verify operator listed in `fiftyone.yml`
- Check `register()` function
- Run `list_operators()` to debug

**Secrets not available:**
- Add to `fiftyone.yml` under `secrets:`
- Set environment variables before starting FiftyOne

**Render loop / thousands of operator calls per minute:**
- Almost always caused by `default=ctx.panel.get_state(...)` — see Gotcha 1 above
- Fix: replace with a string/number literal in `default=`

## Advanced

### Programmatic Operator Execution
```python
# For executing operators outside of FiftyOne App context
import fiftyone.operators as foo
result = foo.execute_operator(operator_uri, ctx, **params)
```

## Resources

- [Plugin Development Guide](https://docs.voxel51.com/plugins/developing_plugins.html)
- [Developing Panels](https://docs.voxel51.com/plugins/developing_plugins.html#developing-panels)
- [Developing JS Plugins](https://docs.voxel51.com/plugins/developing_plugins.html#developing-js-plugins)
- [Panel Examples (reference implementations)](https://github.com/voxel51/fiftyone-plugins/blob/main/plugins/panel-examples/__init__.py)
- [FiftyOne Plugins Repo](https://github.com/voxel51/fiftyone-plugins)
- [Operator Types API](https://docs.voxel51.com/api/fiftyone.operators.types.html)

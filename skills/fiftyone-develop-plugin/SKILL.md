---
name: fiftyone-develop-plugin
description: Develops custom FiftyOne plugins (operators and panels) from scratch. Use when creating plugins, extending FiftyOne with custom operators, building interactive panels, or integrating external APIs.
---

# Develop FiftyOne Plugins

## Key Directives

**ALWAYS follow these rules:**

### 1. Understand before coding
Ask clarifying questions. Never assume what the plugin should do.

### 2. Plan before implementing
Present file structure and design. Get user approval before generating code.

### 3. Search existing plugins for patterns
```python
list_plugins(enabled=True)
list_operators(builtin_only=False)
get_operator_schema(operator_uri="@voxel51/brain/compute_similarity")
```

### 4. Test locally before done
Install plugin and verify it works in FiftyOne App.

### 5. Iterate on feedback
Refine until the plugin works as expected.

## Critical Patterns

### Operator Execution
```python
# Use foo.execute_operator() for programmatic execution
import fiftyone.operators as foo
result = foo.execute_operator(operator_uri, ctx, **params)

# Use ctx.trigger() to chain operators from within an operator
ctx.trigger("@plugin/other_operator", params={...})

# ctx.ops provides UI operations: notify(), set_progress(), show_panel_output()
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
# Use namespaced keys to avoid cross-dataset conflicts
def _get_store_key(self, ctx):
    plugin_name = self.config.name.split("/")[-1]
    return f"{plugin_name}_store_{ctx.dataset._doc.id}_{self.version}"

store = ctx.store(self._get_store_key(ctx))
```

### Panel State vs Execution Store
```python
# ctx.panel.state - Transient (resets when panel reloads)
# ctx.store() - Persistent (survives across sessions)

def on_load(self, ctx):
    ctx.panel.state.selected_tab = "overview"  # Transient
    store = ctx.store(self._get_store_key(ctx))
    ctx.panel.state.config = store.get("user_config") or {}  # Persistent
```

### Delegated Execution
Use for operations that: process >100 samples, take >1 second, or call external APIs.

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

Ask these questions:

1. "What should your plugin do?" (one sentence)
2. "Operator (action) or Panel (interactive UI)?"
3. "What inputs from the user?"
4. "What outputs/results?"
5. "External APIs or secrets needed?"
6. "Background execution for long tasks?"

### Phase 2: Design

1. Search existing plugins for similar patterns
2. Create plan with:
   - Plugin name (`@org/plugin-name`)
   - File structure
   - Operator/panel specs
   - Input/output definitions
3. **Get user approval before coding**

See [PLUGIN-STRUCTURE.md](PLUGIN-STRUCTURE.md) for file formats.

### Phase 3: Generate Code

Create these files:

| File | Required | Purpose |
|------|----------|---------|
| `fiftyone.yml` | Yes | Plugin manifest |
| `__init__.py` | Yes | Python operators/panels |
| `requirements.txt` | If deps | Python dependencies |
| `package.json` | JS only | Node.js metadata |
| `src/index.tsx` | JS only | React components |

Reference docs:
- [PYTHON-OPERATOR.md](PYTHON-OPERATOR.md) - Python operators
- [PYTHON-PANEL.md](PYTHON-PANEL.md) - Python panels
- [JAVASCRIPT-PANEL.md](JAVASCRIPT-PANEL.md) - React/TypeScript panels
- [HYBRID-PLUGINS.md](HYBRID-PLUGINS.md) - Python + JavaScript communication
- [EXECUTION-STORE.md](EXECUTION-STORE.md) - Persistent storage and caching

### Phase 4: Install & Test

#### 4.1 Install Plugin
```bash
# Find plugins directory
python -c "import fiftyone as fo; print(fo.config.plugins_dir)"

# Copy plugin
cp -r ./my-plugin ~/.fiftyone/plugins/
```

#### 4.2 Validate Detection
```python
list_plugins(enabled=True)  # Should show your plugin
list_operators()  # Should show your operators
```

**If not found:** Check fiftyone.yml syntax, Python syntax errors, restart App.

#### 4.3 Validate Schema
```python
get_operator_schema(operator_uri="@myorg/my-operator")
```

Verify inputs/outputs match your expectations.

#### 4.4 Test Execution
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
2. Fix issues
3. Re-copy to plugins directory
4. Restart App if needed
5. Repeat until working

## Quick Reference

### Plugin Types

| Type | Language | Use Case |
|------|----------|----------|
| Operator | Python | Data processing, computations |
| Panel | Python | Simple interactive UI |
| Panel | JavaScript | Rich React-based UI |

### Operator Config Options

| Option | Default | Effect |
|--------|---------|--------|
| `dynamic` | False | Recalculate inputs on change |
| `execute_as_generator` | False | Stream progress with yield |
| `allow_immediate_execution` | True | Execute in foreground |
| `allow_delegated_execution` | False | Background execution |
| `default_choice_to_delegated` | False | Default to background |
| `unlisted` | False | Hide from operator browser |
| `on_startup` | False | Execute when app starts |
| `on_dataset_open` | False | Execute when dataset opens |

### Panel Config Options

| Option | Default | Effect |
|--------|---------|--------|
| `allow_multiple` | False | Allow multiple panel instances |
| `surfaces` | "grid" | Where panel can display ("grid", "modal", "grid modal") |
| `category` | None | Panel category in browser |
| `priority` | None | Sort order in UI |

### Input Types

| Type | Method |
|------|--------|
| Text | `inputs.str()` |
| Number | `inputs.int()` / `inputs.float()` |
| Boolean | `inputs.bool()` |
| Dropdown | `inputs.enum()` |
| File | `inputs.file()` |
| View | `inputs.view_target()` |

## Minimal Example

**fiftyone.yml:**
```yaml
name: "@myorg/hello-world"
type: plugin
operators:
  - hello_world
```

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

## Debugging

### Where Logs Go

| Log Type | Location |
|----------|----------|
| Python backend | Terminal running the server |
| JavaScript frontend | Browser console (F12 → Console) |
| Network requests | Browser DevTools (F12 → Network) |
| Operator errors | Operator browser in FiftyOne App |

### Running Server Separately (Recommended for Development)

To see Python plugin logs, run the server and app separately:

```bash
# Terminal 1: Run FiftyOne server (shows Python logs)
python -m fiftyone.server.main

# Terminal 2: Access the app in browser
# Logs from print() and logging will appear in Terminal 1
```

### Python Debugging

```python
def execute(self, ctx):
    # Use print() for quick debugging (shows in server terminal)
    print(f"Params received: {ctx.params}")
    print(f"Dataset: {ctx.dataset.name}, View size: {len(ctx.view)}")

    # For structured logging
    import logging
    logging.info(f"Processing {len(ctx.target_view())} samples")

    # ... rest of execution
```

### JavaScript/TypeScript Debugging

```typescript
// Use console.log in React components
console.log("Component state:", state);
console.log("Panel data:", panelData);

// Check browser DevTools:
// - Console: JS errors, syntax errors, plugin load failures
// - Network: API calls, variable values before/after execution
```

### Common Debug Locations

- **Operator not executing**: Check Network tab for request/response
- **Plugin not loading**: Check Console for syntax errors
- **Variables not updating**: Check Network tab for payload data
- **Silent failures**: Check Operator browser for error messages

## Troubleshooting

**Plugin not appearing:**
- Check `fiftyone.yml` exists in plugin root
- Verify location: `~/.fiftyone/plugins/`
- Check for Python syntax errors
- Restart FiftyOne App

**Operator not found:**
- Verify operator listed in `fiftyone.yml`
- Check `register()` function
- Run `list_operators()` to debug

**Secrets not available:**
- Add to `fiftyone.yml` under `secrets:`
- Set environment variables before starting FiftyOne

## Resources

- [Plugin Development Guide](https://docs.voxel51.com/plugins/developing_plugins.html)
- [FiftyOne Plugins Repo](https://github.com/voxel51/fiftyone-plugins)
- [Operator Types API](https://docs.voxel51.com/api/fiftyone.operators.types.html)

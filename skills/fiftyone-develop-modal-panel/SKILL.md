---
name: fiftyone-develop-modal-panel
description: Develops custom FiftyOne modal panel plugins with JavaScript UI. Use when building interactive panels that appear in the sample modal — image overlays, per-sample visualizations, annotation tools, or any custom UI that needs to render alongside a sample.
---

# Develop FiftyOne Modal Panel Plugins

## How the FiftyOne Plugin System Works

Understanding the plugin loading lifecycle is essential. Every decision in this
skill flows from this model.

### Plugin discovery

When the FiftyOne App starts, the server scans all plugin directories for
`fiftyone.yml` manifests. Each manifest declares:

- **`panels:`** — panel names the App should show in the panel picker
- **`operators:`** — operator names the server should register for execution
- **`fiftyone.script`** (in `package.json`) — path to the JS bundle to load

The server loads Python code (`__init__.py`) and the `register()` function runs,
registering Operator classes. The App frontend loads each plugin's JS bundle as
a `<script>` tag.

### JS bundle loading

The App discovers JS bundles via `"fiftyone": { "script": "path/to/bundle.js" }`
in `package.json`. When the bundle loads, it executes immediately. Any
`registerComponent()` calls inside the bundle register React components in the
App's component registry.

**Important:** Do NOT use `js_bundle:` in `fiftyone.yml`. Some versions of FiftyOne
do not read this field. The `package.json` `fiftyone.script` field is the reliable
discovery mechanism.

### Panel rendering

When a user opens a panel, the App looks up the component by name in its
registry. For modal panels, the App checks `panelOptions.surfaces` on the
registered component to decide whether to show it in the modal panel picker.

### JS runtime globals

The FiftyOne App exposes its internal modules as window globals before loading
plugin bundles. Your plugin code can import from these packages, and the build
system (vite + externals plugin) replaces those imports with references to the
window globals:

| Package | Window Global | What it provides |
|---------|---------------|------------------|
| `@fiftyone/plugins` | `window.__fop__` | `registerComponent`, `PluginComponentType` |
| `@fiftyone/operators` | `window.__foo__` | `useOperatorExecutor`, `usePanelEvent`, `Operator` |
| `@fiftyone/state` | `window.__fos__` | Recoil atoms for dataset, view, modal state |
| `@fiftyone/components` | `window.__foc__` | FiftyOne UI components |
| `@fiftyone/utilities` | `window.__fou__` | Utility functions |
| `@fiftyone/spaces` | `window.__fosp__` | Panel/space management |
| `@mui/material` | `window.__mui__` | MUI components (Box, Typography, etc.) |
| `react` | `window.React` | React |
| `react-dom` | `window.ReactDOM` | ReactDOM |
| `recoil` | `window.recoil` | `useRecoilValue`, `useSetRecoilState`, `atom` |

Because these are provided at runtime, you must **externalize** them in your
build config so they are NOT bundled into your plugin. If they get bundled,
you'll have duplicate React instances and the App will crash or behave
unpredictably.

---

## Architecture: JS Panel + Python Operators

Modal panels use a split architecture:

- **React component (JS)** — handles all UI rendering, user interaction, and
  state. Registered via `registerComponent()` with `panelOptions: { surfaces: "modal" }`.
- **Python operators** — handle backend data access (dataset queries, sample
  lookups, aggregations). Marked `unlisted=True` so they don't appear in the
  operator browser. Called from JS via `useOperatorExecutor`.

### Why not Python Panels?

FiftyOne has a Python Panel system (`foo.Panel` / `PanelConfig`), but it has
critical limitations for modal use:

1. **No image display** — `panel.image()` and `panel.media()` do not exist in
   the Python Panel API. You can show Plotly charts and markdown, but not
   images or custom visualizations.
2. **`composite_view=True` is broken** — Python Panels can declare
   `composite_view=True` to delegate rendering to a JS component, but this
   produces "Unsupported View" errors because the App cannot match the
   component name to the JS registry in practice.
3. **No client-side interactivity** — sliders, hover effects, drag, canvas
   operations, and real-time visual feedback all require JS.

### Why not a pure JS panel without Python operators?

You could write a panel that's 100% JS with no Python backend. However, most
useful modal panels need to:

- Query dataset fields and values
- Access the current sample's metadata
- Run aggregations or computations on the dataset

These operations require the FiftyOne Python SDK, which is only available
server-side. Python operators bridge this gap — they run on the server with
full `ctx.dataset` access and return JSON results to the JS frontend.

---

## How `registerComponent` Works for Modal Panels

```typescript
registerComponent({
  name: "MyModalPanel",                    // Unique name — must match fiftyone.yml panels entry
  label: "My Modal Panel",                 // Display name in the panel picker
  component: MyReactComponent,             // The React component to render
  type: PluginComponentType.Panel,         // Tells the App this is a panel (not a plot/visualizer)
  panelOptions: { surfaces: "modal" },     // WHERE the panel appears
});
```

**`panelOptions: { surfaces: "modal" }`** is how the App knows this panel
belongs in the sample modal. Without this, the panel appears in the grid view
instead. Note: `surfaces: "modal"` at the top level of the options object does
NOT work — it must be nested inside `panelOptions`.

Valid surface values: `"grid"`, `"modal"`, `"grid modal"` (both).

The `name` field must exactly match the entry in `fiftyone.yml` under `panels:`.
If these don't match, the App either won't show the panel in the picker or
won't be able to render it.

---

## How `useOperatorExecutor` Works

`useOperatorExecutor` is a React hook that manages operator execution lifecycle:

```typescript
const myOp = useOperatorExecutor("@myorg/my-plugin/my_operator");
```

It returns an object with:
- `execute(params)` — triggers operator execution. **Returns void**, not the result.
- `result` — the operator's return value, populated after execution completes.
  This is a React state variable, so changing it triggers a re-render.
- `error` — any error from the execution.
- `isLoading` / `isExecuting` — boolean flags.

Because `execute()` returns void, you cannot chain `.then()` on it to read the
result. Instead, use a `useEffect` that watches the `result` property:

```typescript
// Trigger execution
useEffect(() => { myOp.execute({}); }, []);

// React to the result when it arrives
useEffect(() => {
  if (myOp.result?.myField) {
    setMyState(myOp.result.myField);
  }
}, [myOp.result]);
```

The operator's Python `execute()` return dict becomes `myOp.result` directly.
If Python returns `{"filepaths": [...]}`, JS sees `myOp.result.filepaths`.

---

## How `ctx.current_sample` Works in Operators

When a Python operator is executed from a modal context, `ctx.current_sample`
contains the **sample ID** (a string), not a Sample object. To access sample
fields:

```python
sample_id = ctx.current_sample           # "6507a1b2c3d4e5f6..."
sample = ctx.dataset[sample_id]          # fiftyone.core.sample.Sample
filepath = sample.filepath               # "/path/to/image.jpg"
```

If you try `ctx.current_sample.filepath` directly, you'll get an
`AttributeError` because you're calling `.filepath` on a string.

Other useful context properties in operators:
- `ctx.dataset` — the current Dataset object
- `ctx.view` — the current view (with any filters applied)
- `ctx.selected` — list of explicitly selected (checked) sample IDs
- `ctx.params` — parameters passed from JS via `execute({...})`

---

## How the Build System Works

FiftyOne JS plugins are built as UMD bundles using Vite. The key configuration
is the **externals** — telling Vite to replace `import { X } from "@fiftyone/Y"`
with references to `window.__foY__` instead of bundling the package.

This is done via `vite-plugin-externals`:

```typescript
viteExternalsPlugin({
  react: "React",                    // import React → window.React
  "react-dom": "ReactDOM",
  "@fiftyone/state": "__fos__",      // import * as fos → window.__fos__
  "@fiftyone/operators": "__foo__",
  "@fiftyone/plugins": "__fop__",
  // ... etc
})
```

The `fiftyonePlugin()` in the vite config is a dev-time convenience — if you
set `FIFTYONE_DIR` to your local FiftyOne source checkout, it resolves
`@fiftyone/*` imports to the local packages for type checking. It's optional
and has no effect on the production build.

**Use Yarn 4.x**, not npm. FiftyOne plugin repositories use Yarn for package
management. npm may fail to resolve peer dependencies correctly.

---

## Media URLs

FiftyOne serves sample media through a `/media` endpoint. To display an image
in your JS panel, construct a URL from the filepath:

```typescript
function getMediaUrl(filepath: string): string {
  return `/media?filepath=${encodeURIComponent(filepath)}`;
}

// In JSX
<img src={getMediaUrl(sample.filepath)} />
```

This works for local paths (`/data/images/001.jpg`) and cloud storage
(`s3://bucket/image.jpg`) — the FiftyOne server handles proxying and
authentication.

---

## Complete File-by-File Reference

Every file you need to create, with explanations.

### fiftyone.yml

```yaml
name: "@myorg/my-modal-plugin"
type: plugin                     # Required by some FiftyOne versions
version: "1.0.0"
description: "My custom modal panel"
fiftyone:
  version: "*"
panels:
  - MyModalPanel                 # Must exactly match registerComponent name
operators:
  - get_data                     # Must exactly match Operator.config.name
  - get_current_sample
```

### package.json

```json
{
  "name": "@myorg/my-modal-plugin",
  "version": "1.0.0",
  "main": "src/index.ts",
  "fiftyone": {
    "script": "dist/index.umd.js"
  },
  "scripts": {
    "build": "vite build",
    "dev": "IS_DEV=true vite build --watch"
  },
  "dependencies": {
    "@rollup/plugin-node-resolve": "^15.0.2",
    "@vitejs/plugin-react": "^4.0.0",
    "react": "^18.2.0",
    "vite-plugin-externals": "^0.6.2"
  },
  "devDependencies": {
    "typescript": "^5.0.0",
    "vite": "^5.0.0"
  },
  "packageManager": "yarn@4.10.3"
}
```

### __init__.py

```python
import fiftyone.operators as foo
import fiftyone.operators.types as types


class GetData(foo.Operator):
    """Backend operator called by the JS panel to fetch dataset data."""

    @property
    def config(self):
        return foo.OperatorConfig(
            name="get_data",
            label="Get Data",
            unlisted=True,       # Hide from operator browser — internal use only
        )

    def execute(self, ctx):
        values = ctx.dataset.values("filepath")
        return {"values": values}  # This dict becomes myOp.result in JS


class GetCurrentSample(foo.Operator):
    """Returns the current modal sample's data."""

    @property
    def config(self):
        return foo.OperatorConfig(
            name="get_current_sample",
            label="Get Current Sample",
            unlisted=True,
        )

    def execute(self, ctx):
        try:
            sample_id = ctx.current_sample          # String ID, not a Sample
            if sample_id:
                sample = ctx.dataset[sample_id]     # Fetch the Sample object
                return {"filepath": sample.filepath, "id": sample_id}
        except Exception:
            pass
        return {"filepath": None, "id": None}


def register(p):
    p.register(GetData)
    p.register(GetCurrentSample)
```

### vite.config.ts

```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { nodeResolve } from "@rollup/plugin-node-resolve";
import { viteExternalsPlugin } from "vite-plugin-externals";
import path from "path";
import pkg from "./package.json";

const { FIFTYONE_DIR } = process.env;
const IS_DEV = process.env.IS_DEV === "true";

// Dev-time only: resolve @fiftyone/* from local source for type checking
function fiftyonePlugin() {
  return {
    name: "fiftyone-rollup",
    resolveId: {
      order: "pre" as const,
      async handler(source: string) {
        if (source.startsWith("@fiftyone") && FIFTYONE_DIR) {
          const pkgName = source.split("/")[1];
          const modulePath = `${FIFTYONE_DIR}/app/packages/${pkgName}`;
          return this.resolve(modulePath, source, { skipSelf: true });
        }
        return null;
      },
    },
  };
}

export default defineConfig({
  mode: IS_DEV ? "development" : "production",
  plugins: [
    fiftyonePlugin(),
    nodeResolve(),
    react(),
    // Replace imports with window global references
    viteExternalsPlugin({
      react: "React",
      "react-dom": "ReactDOM",
      "@fiftyone/state": "__fos__",
      "@fiftyone/operators": "__foo__",
      "@fiftyone/components": "__foc__",
      "@fiftyone/utilities": "__fou__",
      "@fiftyone/plugins": "__fop__",
      "@fiftyone/spaces": "__fosp__",
    }),
  ],
  build: {
    minify: !IS_DEV,
    lib: {
      entry: path.join(__dirname, pkg.main),
      name: pkg.name,
      fileName: (format) => `index.${format}.js`,
      formats: ["umd"],
    },
  },
  define: {
    "process.env.NODE_ENV": JSON.stringify(
      IS_DEV ? "development" : "production"
    ),
  },
  optimizeDeps: {
    exclude: ["react", "react-dom"],
  },
});
```

### tsconfig.json

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "jsx": "react-jsx",
    "moduleResolution": "Node",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true
  },
  "include": ["src"]
}
```

### src/index.ts

```typescript
import { PluginComponentType, registerComponent } from "@fiftyone/plugins";
import MyModalPanel from "./MyPanel";

// This log confirms the bundle loaded — check browser console
console.log("[MyPlugin] Registering MyModalPanel");

registerComponent({
  name: "MyModalPanel",
  label: "My Modal Panel",
  component: MyModalPanel,
  type: PluginComponentType.Panel,
  panelOptions: { surfaces: "modal" },
});
```

### src/MyPanel.tsx

```typescript
import React, { useState, useEffect, useRef, useCallback } from "react";
import { useOperatorExecutor } from "@fiftyone/operators";

const PLUGIN = "@myorg/my-modal-plugin";

function getMediaUrl(filepath: string): string {
  return `/media?filepath=${encodeURIComponent(filepath)}`;
}

export default function MyModalPanel() {
  const dataOp = useOperatorExecutor(`${PLUGIN}/get_data`);
  const sampleOp = useOperatorExecutor(`${PLUGIN}/get_current_sample`);

  const [data, setData] = useState<string[]>([]);
  const [currentSample, setCurrentSample] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const hasTriggered = useRef(false);

  // Fire operators once on mount
  useEffect(() => {
    if (hasTriggered.current) return;
    hasTriggered.current = true;
    dataOp.execute({});
    sampleOp.execute({});
  }, []);

  // Watch for data result (fires when dataOp.result state changes)
  useEffect(() => {
    if (dataOp.result?.values) {
      setData(dataOp.result.values);
      setLoading(false);
    }
  }, [dataOp.result]);

  // Watch for current sample result
  useEffect(() => {
    if (sampleOp.result?.filepath) {
      setCurrentSample(sampleOp.result);
    }
  }, [sampleOp.result]);

  useEffect(() => {
    if (dataOp.error) {
      console.error("[MyPlugin] Error:", dataOp.error);
      setLoading(false);
    }
  }, [dataOp.error]);

  const refresh = useCallback(() => {
    sampleOp.execute({});
  }, [sampleOp]);

  if (loading) {
    return <div style={{ padding: 16, color: "#888" }}>Loading…</div>;
  }

  return (
    <div style={{ padding: 16, color: "#e0e0e0", fontFamily: "system-ui" }}>
      <h3>My Modal Panel</h3>

      {currentSample?.filepath && (
        <img
          src={getMediaUrl(currentSample.filepath)}
          alt="current"
          style={{ maxWidth: "100%", borderRadius: 4 }}
        />
      )}

      <button onClick={refresh} style={{ marginTop: 8 }}>
        Refresh Sample
      </button>

      <p>{data.length} items loaded</p>
    </div>
  );
}
```

---

## Build & Development Workflow

```bash
cd my-modal-plugin

# Install dependencies — MUST use yarn, not npm
yarn install

# Build the JS bundle
yarn build

# Verify the bundle was created
ls dist/index.umd.js

# Restart the FiftyOne App, then open a sample modal
# The panel should appear in the modal panel picker
```

### Iterating during development

```bash
# Terminal 1: auto-rebuild on file changes
yarn dev

# Terminal 2: FiftyOne with server logs visible
fiftyone app debug <dataset-name>

# After each rebuild: hard-refresh browser (Ctrl+Shift+R)
# Check browser console (F12) for [MyPlugin] registration log
# Check server terminal for Python operator logs
```

---

## Patterns

### Dropdown populated from dataset values

```python
# Python operator
class GetFieldValues(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(name="get_field_values", unlisted=True)

    def execute(self, ctx):
        return {"values": ctx.dataset.distinct("label")}
```

```typescript
// JS component
const fieldOp = useOperatorExecutor("@myorg/plugin/get_field_values");

useEffect(() => { fieldOp.execute({}); }, []);
useEffect(() => {
  if (fieldOp.result?.values) setOptions(fieldOp.result.values);
}, [fieldOp.result]);

return (
  <select onChange={(e) => setSelected(e.target.value)}>
    {options.map(v => <option key={v} value={v}>{v}</option>)}
  </select>
);
```

### Passing parameters from JS to Python

```python
class GetSampleField(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(name="get_sample_field", unlisted=True)

    def resolve_input(self, ctx):
        inputs = types.Object()
        inputs.str("sample_id", required=True)
        inputs.str("field", required=True)
        return types.Property(inputs)

    def execute(self, ctx):
        sample = ctx.dataset[ctx.params["sample_id"]]
        return {"value": sample[ctx.params["field"]]}
```

```typescript
fieldOp.execute({ sample_id: "abc123", field: "predictions" });
```

### CSS image overlay (client-side, no server round-trip)

```typescript
<div style={{ position: "relative", width: "100%", height: "100%" }}>
  <img src={baseSrc} style={{
    position: "absolute", top: "50%", left: "50%",
    transform: "translate(-50%, -50%)",
    maxWidth: "100%", maxHeight: "100%", objectFit: "contain",
  }} />
  <img src={overlaySrc} style={{
    position: "absolute", top: "50%", left: "50%",
    transform: "translate(-50%, -50%)",
    maxWidth: "100%", maxHeight: "100%", objectFit: "contain",
    opacity: sliderValue / 100,
    mixBlendMode: diffMode ? "difference" : "normal",
    pointerEvents: "none",
  }} />
</div>
```

---

## Debugging

| Symptom | Cause | Fix |
|---------|-------|-----|
| Panel not in modal picker | `panelOptions` missing or wrong | Use `panelOptions: { surfaces: "modal" }` — NOT `surfaces: "modal"` at top level |
| Panel not in modal picker | Name mismatch | `fiftyone.yml` `panels:` entry must exactly match `registerComponent` `name` |
| Panel not in modal picker | Bundle not loaded | Check `fiftyone.script` in `package.json` points to existing built file |
| "Unsupported View" error | Using `composite_view=True` | Don't — use JS panel + Python operators instead |
| Bundle not loading | No registration log in console | Restart FiftyOne server; verify `dist/index.umd.js` exists |
| Dropdown/data empty | Chaining `.then()` on execute | Watch `executor.result` via `useEffect` instead |
| `AttributeError` on current sample | Treating ID as Sample | `ctx.current_sample` is a string ID — use `ctx.dataset[ctx.current_sample]` |
| `npm install` fails | Wrong package manager | Use `yarn install` (Yarn 4.x) |
| Duplicate React errors | `@fiftyone/*` bundled | Externalize all FiftyOne packages in vite config |
| `type: plugin` missing | fiftyone.yml incomplete | Add `type: plugin` — some FiftyOne versions require it |

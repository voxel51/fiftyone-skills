# JavaScript Panel Development

## Contents
- [Overview](#overview)
- [When to Use JavaScript Panels](#when-to-use-javascript-panels)
- [Project Setup](#project-setup)
- [Component Registration](#component-registration)
- [React Component Development](#react-component-development)
- [Styling](#styling)
- [TypeScript Operators](#typescript-operators)
- [Building and Installing](#building-and-installing)
- [Complete Example](#complete-example-sample-browser-panel)
- [Modal Panels](#modal-panels)
- [Debugging JavaScript Panels](#debugging-javascript-panels)
- [Troubleshooting](#troubleshooting)

---

## Overview

JavaScript panels provide rich, interactive UIs using React and the FiftyOne JavaScript SDK. They offer more flexibility than Python panels but require additional setup.

## When to Use JavaScript Panels

Use JavaScript panels when you need:
- Complex interactive visualizations
- Custom React components
- Real-time updates without page refresh
- Integration with existing React libraries
- Advanced styling with CSS/Tailwind

For simpler UIs, prefer Python panels.

## Project Setup

### Directory Structure

```
my-js-plugin/
├── fiftyone.yml          # Plugin manifest
├── package.json          # Node.js dependencies
├── tsconfig.json         # TypeScript config
├── vite.config.ts        # Build configuration
├── src/
│   ├── index.tsx         # Main entry point
│   └── components/       # React components
│       └── MyPanel.tsx
└── dist/
    └── index.umd.js      # Compiled bundle
```

### fiftyone.yml

```yaml
name: "@myorg/js-panel"
type: plugin
version: 1.0.0
panels:
  - my_panel
```

### package.json

```json
{
  "name": "@myorg/js-panel",
  "version": "1.0.0",
  "main": "dist/index.umd.js",
  "scripts": {
    "build": "vite build",
    "dev": "vite build --watch"
  },
  "dependencies": {
    "@fiftyone/components": "*",
    "@fiftyone/operators": "*",
    "@fiftyone/plugins": "*",
    "@fiftyone/state": "*",
    "@voxel51/voodo": "latest"
  },
  "devDependencies": {
    "@types/react": "^18.0.0",
    "react": "^18.0.0",
    "typescript": "^5.0.0",
    "vite": "^5.0.0"
  },
  "peerDependencies": {
    "react": "^18.0.0",
    "react-dom": "^18.0.0"
  }
}
```

### vite.config.ts

```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  build: {
    lib: {
      entry: "src/index.tsx",
      name: "MyPlugin",
      fileName: "index",
      formats: ["umd"],
    },
    rollupOptions: {
      external: [
        "react",
        "react-dom",
        "@fiftyone/components",
        "@fiftyone/operators",
        "@fiftyone/plugins",
        "@fiftyone/state",
        "recoil",
      ],
      output: {
        globals: {
          react: "React",
          "react-dom": "ReactDOM",
          recoil: "recoil",
          "@fiftyone/components": "__foc__",
          "@fiftyone/operators": "__foo__",
          "@fiftyone/plugins": "__fop__",
          "@fiftyone/state": "__fos__",
        },
      },
    },
  },
});
```

## Component Registration

### Grid panels

```typescript
import { registerComponent, PluginComponentType } from "@fiftyone/plugins";
import MyPanel from "./components/MyPanel";

registerComponent({
  name: "my_panel",           // Must match fiftyone.yml
  label: "My Panel",          // Display name
  component: MyPanel,         // React component
  type: PluginComponentType.Panel,
  activator: ({ dataset }) => {
    return dataset !== null;
  },
  surfaces: "grid",           // Top-level surfaces works for grid panels
});
```

### Modal panels

For panels that appear in the **sample modal**, you MUST use `panelOptions`:

```typescript
registerComponent({
  name: "MyModalPanel",
  label: "My Modal Panel",
  component: MyModalPanel,
  type: PluginComponentType.Panel,
  panelOptions: { surfaces: "modal" },   // MUST be nested in panelOptions
});

// WRONG — this will NOT show the panel in the modal picker:
// surfaces: "modal"  (top-level does not work for modal panels)
```

See the [Modal Panels](#modal-panels) section below for the full architecture.

## React Component Development

### Basic Panel Component

```typescript
// src/components/MyPanel.tsx
import React from "react";
import { useRecoilValue } from "recoil";
import * as fos from "@fiftyone/state";
import { Button } from "@fiftyone/components";

const MyPanel: React.FC = () => {
  // Access FiftyOne state
  const dataset = useRecoilValue(fos.dataset);
  const view = useRecoilValue(fos.view);
  const selected = useRecoilValue(fos.selectedSamples);

  return (
    <div style={{ padding: "16px" }}>
      <h2>My Panel</h2>
      <p>Dataset: {dataset?.name}</p>
      <p>Samples in view: {view?.length ?? 0}</p>
      <p>Selected: {selected.size}</p>
      <Button onClick={() => console.log("Clicked!")}>
        Click Me
      </Button>
    </div>
  );
};

export default MyPanel;
```

### Using FiftyOne State

```typescript
import { useRecoilValue, useSetRecoilState } from "recoil";
import * as fos from "@fiftyone/state";

const MyComponent: React.FC = () => {
  // Read state
  const dataset = useRecoilValue(fos.dataset);
  const view = useRecoilValue(fos.view);
  const selected = useRecoilValue(fos.selectedSamples);
  const filters = useRecoilValue(fos.filters);

  // Write state
  const setSelected = fos.useSetSelected();
  const setView = fos.useSetView();

  const handleSelectAll = () => {
    // Select all samples in current view
    if (view) {
      const ids = view.map((s) => s.id);
      setSelected(ids);
    }
  };

  const handleClearFilters = () => {
    setView([]);  // Reset to full dataset
  };

  return (
    <div>
      <button onClick={handleSelectAll}>Select All</button>
      <button onClick={handleClearFilters}>Clear Filters</button>
    </div>
  );
};
```

### Panel State Management

```typescript
import React, { useState, useEffect } from "react";
import { usePanelState } from "@fiftyone/state";

const StatefulPanel: React.FC = () => {
  // Use panel-scoped state that persists across renders
  const [count, setCount] = usePanelState("count", 0);
  const [config, setConfig] = usePanelState("config", { theme: "light" });

  // Local state (resets on re-render)
  const [localValue, setLocalValue] = useState("");

  return (
    <div>
      <p>Persistent count: {count}</p>
      <button onClick={() => setCount(count + 1)}>Increment</button>

      <p>Config theme: {config.theme}</p>
      <button onClick={() => setConfig({ ...config, theme: "dark" })}>
        Toggle Theme
      </button>
    </div>
  );
};
```

### Triggering Operators

```typescript
import { useOperatorExecutor } from "@fiftyone/operators";

const OperatorTrigger: React.FC = () => {
  const executor = useOperatorExecutor("@voxel51/brain/compute_similarity");

  const handleCompute = async () => {
    executor.execute({
      brain_key: "my_similarity",
      model: "clip-vit-base32-torch",
    });
  };

  return (
    <button onClick={handleCompute} disabled={executor.isLoading}>
      {executor.isLoading ? "Computing..." : "Compute Similarity"}
    </button>
  );
};
```

### Reading operator results

`execute()` returns **void** — it triggers execution asynchronously and populates
`executor.result` via React state when done. Do NOT chain `.then()` on it.
Instead, watch the `.result` property with `useEffect`:

```typescript
const dataOp = useOperatorExecutor("@myorg/plugin/get_data");

// Trigger once on mount
useEffect(() => { dataOp.execute({}); }, []);

// React to the result when it arrives
useEffect(() => {
  if (dataOp.result?.values) {
    setMyState(dataOp.result.values);
  }
}, [dataOp.result]);

// Handle errors
useEffect(() => {
  if (dataOp.error) console.error("Operator failed:", dataOp.error);
}, [dataOp.error]);
```

The Python operator's `execute()` return dict becomes `dataOp.result` directly —
if Python returns `{"values": [...]}`, JS reads `dataOp.result.values`.

## Styling

### Using VOODO Components (Recommended)

**VOODO** is FiftyOne's official React component library. Use it for consistent, theme-aware UI components.

```bash
npm install @voxel51/voodo
```

```typescript
import { Button, Input, Select, Toast, Stack, Heading, Text } from "@voxel51/voodo";

const MyPanel: React.FC = () => {
  return (
    <Stack spacing="md">
      <Heading level={2}>Panel Title</Heading>
      <Input placeholder="Enter value..." />
      <Button variant="primary">Submit</Button>
    </Stack>
  );
};
```

**For complete VOODO documentation**: Invoke the `fiftyone-voodo-design` skill, which:
- Fetches current components from llms.txt
- Lists design tokens (colors, spacing, typography)
- Provides usage patterns and Storybook links

**Quick reference**: https://voodo.dev.fiftyone.ai/

### Using Tailwind CSS

```typescript
import "@fiftyone/components/dist/styles.css";  // Base styles

const StyledPanel: React.FC = () => {
  return (
    <div className="p-4 bg-gray-100 rounded-lg">
      <h2 className="text-lg font-bold mb-2">Styled Panel</h2>
      <p className="text-gray-600">This uses Tailwind classes</p>
    </div>
  );
};
```

### Using CSS-in-JS

```typescript
const styles = {
  container: {
    padding: "16px",
    backgroundColor: "#f5f5f5",
    borderRadius: "8px",
  },
  title: {
    fontSize: "18px",
    fontWeight: "bold",
    marginBottom: "8px",
  },
};

const StyledPanel: React.FC = () => {
  return (
    <div style={styles.container}>
      <h2 style={styles.title}>Styled Panel</h2>
    </div>
  );
};
```

## TypeScript Operators

You can define operators in TypeScript to interact with React state:

```typescript
import { Operator, OperatorConfig, registerOperator } from "@fiftyone/operators";
import * as fos from "@fiftyone/state";

class SelectRandomSamples extends Operator {
  get config(): OperatorConfig {
    return new OperatorConfig({
      name: "select_random_samples",
      label: "Select Random Samples",
    });
  }

  useHooks() {
    return {
      setSelected: fos.useSetSelected(),
    };
  }

  async execute({ hooks, params }) {
    const { count = 10 } = params;
    // Get random sample IDs (simplified example)
    const randomIds = ["sample1", "sample2", "sample3"].slice(0, count);
    hooks.setSelected(randomIds);
    return { selected: randomIds.length };
  }
}

registerOperator(SelectRandomSamples, "@myorg/my-plugin");
```

### TypeScript Operators as Event Handlers

TypeScript operators can receive triggers from Python operators. Use this pattern for real-time updates:

```typescript
import { Operator, OperatorConfig, registerOperator } from "@fiftyone/operators";
import { useSetRecoilState } from "recoil";
import { progressAtom } from "./state/progress";

class ProgressUpdateOperator extends Operator {
  get config(): OperatorConfig {
    return new OperatorConfig({
      name: "progress_update",
      label: "Progress Update",
      unlisted: true,  // Hide from operator browser - this is an event handler
    });
  }

  useHooks() {
    const setProgress = useSetRecoilState(progressAtom);
    return { setProgress };
  }

  async execute({ hooks, params }) {
    // Update React state when Python triggers this operator
    hooks.setProgress((prev) => ({
      ...prev,
      value: params.progress ?? prev.value,
      message: params.message ?? prev.message,
    }));
  }
}

// Register with your plugin namespace
registerOperator(ProgressUpdateOperator, "@myorg/my-plugin");
```

Python triggers this operator:
```python
ctx.trigger("@myorg/my-plugin/progress_update", {"progress": 0.5, "message": "Processing..."})
```

See [HYBRID-PLUGINS.md](HYBRID-PLUGINS.md) for complete Python + JavaScript communication patterns.

## Building and Installing

### Development Build

```bash
npm install
npm run dev  # Watch mode - rebuilds on changes
```

### Production Build

```bash
npm run build
```

### Installing Plugin

```bash
# Copy to FiftyOne plugins directory
cp -r ./my-js-plugin ~/.fiftyone/plugins/

# Or install from GitHub
fiftyone plugins download https://github.com/org/my-js-plugin
```

### Hot Reload During Development

```bash
# Terminal 1: Watch for changes
cd my-js-plugin
npm run dev

# Terminal 2: Symlink plugin
ln -s $(pwd) ~/.fiftyone/plugins/my-js-plugin

# Refresh FiftyOne App in browser to see changes
```

## Complete Example: Sample Browser Panel

```typescript
// src/index.tsx
import { registerComponent, PluginComponentTypes } from "@fiftyone/plugins";
import SampleBrowser from "./components/SampleBrowser";

registerComponent({
  name: "sample_browser",
  label: "Sample Browser",
  component: SampleBrowser,
  type: PluginComponentType.Panel,
  activator: ({ dataset }) => dataset !== null,
  surfaces: "grid",  // For modal panels, use panelOptions: { surfaces: "modal" } instead
});
```

```typescript
// src/components/SampleBrowser.tsx
import React, { useState, useEffect } from "react";
import { useRecoilValue } from "recoil";
import * as fos from "@fiftyone/state";
import { Button, Input, Select } from "@fiftyone/components";

interface Sample {
  id: string;
  filepath: string;
  [key: string]: any;
}

const SampleBrowser: React.FC = () => {
  const dataset = useRecoilValue(fos.dataset);
  const view = useRecoilValue(fos.view);
  const selected = useRecoilValue(fos.selectedSamples);
  const setSelected = fos.useSetSelected();

  const [searchTerm, setSearchTerm] = useState("");
  const [sortField, setSortField] = useState("filepath");
  const [filteredSamples, setFilteredSamples] = useState<Sample[]>([]);

  // Get field names for sorting
  const fieldNames = Object.keys(dataset?.sampleFields || {});

  useEffect(() => {
    if (view) {
      // Filter samples by search term
      const filtered = view.filter((sample: Sample) =>
        sample.filepath.toLowerCase().includes(searchTerm.toLowerCase())
      );

      // Sort samples
      filtered.sort((a: Sample, b: Sample) => {
        const aVal = a[sortField] || "";
        const bVal = b[sortField] || "";
        return String(aVal).localeCompare(String(bVal));
      });

      setFilteredSamples(filtered);
    }
  }, [view, searchTerm, sortField]);

  const handleSelectSample = (id: string) => {
    const newSelected = new Set(selected);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelected(Array.from(newSelected));
  };

  const handleSelectAll = () => {
    setSelected(filteredSamples.map((s) => s.id));
  };

  const handleClearSelection = () => {
    setSelected([]);
  };

  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-4">Sample Browser</h2>

      {/* Controls */}
      <div className="flex gap-4 mb-4">
        <Input
          placeholder="Search by filepath..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="flex-1"
        />

        <Select
          value={sortField}
          onChange={(e) => setSortField(e.target.value)}
        >
          {fieldNames.map((field) => (
            <option key={field} value={field}>
              Sort by: {field}
            </option>
          ))}
        </Select>
      </div>

      {/* Selection controls */}
      <div className="flex gap-2 mb-4">
        <Button onClick={handleSelectAll}>Select All</Button>
        <Button onClick={handleClearSelection} variant="secondary">
          Clear Selection
        </Button>
        <span className="ml-auto text-gray-600">
          {selected.size} of {filteredSamples.length} selected
        </span>
      </div>

      {/* Sample list */}
      <div className="border rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-100">
            <tr>
              <th className="p-2 text-left">Select</th>
              <th className="p-2 text-left">ID</th>
              <th className="p-2 text-left">Filepath</th>
            </tr>
          </thead>
          <tbody>
            {filteredSamples.slice(0, 100).map((sample) => (
              <tr
                key={sample.id}
                className={`border-t ${
                  selected.has(sample.id) ? "bg-blue-50" : ""
                }`}
              >
                <td className="p-2">
                  <input
                    type="checkbox"
                    checked={selected.has(sample.id)}
                    onChange={() => handleSelectSample(sample.id)}
                  />
                </td>
                <td className="p-2 font-mono text-sm">
                  {sample.id.slice(0, 8)}...
                </td>
                <td className="p-2 text-sm">{sample.filepath}</td>
              </tr>
            ))}
          </tbody>
        </table>

        {filteredSamples.length > 100 && (
          <div className="p-4 text-center text-gray-500 border-t">
            Showing 100 of {filteredSamples.length} samples
          </div>
        )}
      </div>
    </div>
  );
};

export default SampleBrowser;
```

## Modal Panels

Modal panels appear inside the FiftyOne sample modal. They use a split
architecture: a **React component** for the UI and **Python operators** for
backend data access. No Python Panel class is needed.

### Why not Python Panels for modal?

- `panel.image()` / `panel.media()` do not exist — Python panels cannot display images
- `composite_view=True` produces "Unsupported View" errors in the modal
- Sliders, hover effects, canvas ops, and real-time visual feedback require JS

### Architecture

The JS component is registered with `panelOptions: { surfaces: "modal" }` and
listed under `panels:` in `fiftyone.yml`. Python operators (with `unlisted=True`)
handle dataset queries and are called from JS via `useOperatorExecutor`.

### How the plugin system loads modal panels

1. Server reads `fiftyone.yml` — the `panels:` list tells it which panel names exist
2. App reads `"fiftyone": { "script": "dist/index.umd.js" }` from `package.json`
   and loads the bundle as a `<script>` tag. (Do NOT use `js_bundle:` in
   fiftyone.yml — it is unreliable.)
3. `registerComponent()` in the bundle registers the React component
4. The modal panel picker shows panels whose `panelOptions.surfaces` includes
   `"modal"` AND whose name appears in some plugin's `panels:` list

Both the `panels:` entry and the `panelOptions` registration are required.

### Accessing the current modal sample

`ctx.current_sample` in a Python operator returns the **sample ID** (a string),
not a Sample object:

```python
sample_id = ctx.current_sample           # "6507a1b2c3d4e5f6..."
sample = ctx.dataset[sample_id]          # Fetch the Sample object
filepath = sample.filepath
# WRONG: ctx.current_sample.filepath → AttributeError (it's a string)
```

### Media URLs and signed URLs

For **local development**, media is served at `/media?filepath=...`.

For **Enterprise / cloud storage** (GCS, S3), filepaths like `gs://bucket/image.jpg`
cannot be loaded by the browser directly. The FiftyOne server exposes a
`/signed-url` endpoint that converts cloud paths to time-limited signed HTTPS URLs.

Use this universal helper in your panel to handle all deployment scenarios:

```typescript
import { getFetchParameters } from "@fiftyone/utilities";

async function resolveMediaUrl(filepath: string): Promise<string> {
  // Already a usable HTTP(S) URL — return as-is
  if (filepath.startsWith("http://") || filepath.startsWith("https://")) {
    return filepath;
  }

  const params = getFetchParameters();
  const prefix = (params.pathPrefix || "").replace(/\/+$/, "");

  // Cloud path (gs://, s3://, etc.) — get a signed URL from the server
  if (filepath.includes("://")) {
    try {
      const qp = new URLSearchParams({ cloud_path: filepath });
      const url = `${params.origin}${prefix}/signed-url?${qp}`;
      const res = await fetch(url, {
        headers: params.headers as Record<string, string>,
      });
      const data = await res.json();
      if (data.signed_url) return data.signed_url;
    } catch (e) {
      console.error("Failed to get signed URL:", filepath, e);
    }
    return filepath;
  }

  // Local path — use the /media endpoint
  const path = `${prefix}/media`.replace(/\/\//g, "/");
  return `${params.origin}${path}?filepath=${encodeURIComponent(filepath)}`;
}
```

Because this is async, resolve URLs in `useEffect` and store in state:

```typescript
const [imgSrc, setImgSrc] = useState<string | null>(null);
useEffect(() => {
  if (filepath) resolveMediaUrl(filepath).then(setImgSrc);
}, [filepath]);
return imgSrc ? <img src={imgSrc} /> : null;
```

### Complete modal panel example

**fiftyone.yml:**
```yaml
name: "@myorg/my-modal-plugin"
type: plugin
version: "1.0.0"
fiftyone:
  version: "*"
panels:
  - MyModalPanel                 # Must match registerComponent name
operators:
  - get_data
  - get_current_sample
```

**__init__.py:**
```python
import fiftyone.operators as foo
import fiftyone.operators.types as types

class GetData(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(name="get_data", unlisted=True)

    def execute(self, ctx):
        return {"values": ctx.dataset.values("filepath")}

class GetCurrentSample(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(name="get_current_sample", unlisted=True)

    def execute(self, ctx):
        try:
            sample_id = ctx.current_sample
            if sample_id:
                sample = ctx.dataset[sample_id]
                return {"filepath": sample.filepath, "id": sample_id}
        except Exception:
            pass
        return {"filepath": None, "id": None}

def register(p):
    p.register(GetData)
    p.register(GetCurrentSample)
```

**src/index.ts:**
```typescript
import { PluginComponentType, registerComponent } from "@fiftyone/plugins";
import MyModalPanel from "./MyPanel";

registerComponent({
  name: "MyModalPanel",
  label: "My Modal Panel",
  component: MyModalPanel,
  type: PluginComponentType.Panel,
  panelOptions: { surfaces: "modal" },
});
```

**src/MyPanel.tsx:**
```typescript
import React, { useState, useEffect, useRef, useCallback } from "react";
import { useOperatorExecutor } from "@fiftyone/operators";
import { getFetchParameters } from "@fiftyone/utilities";

const PLUGIN = "@myorg/my-modal-plugin";

async function resolveMediaUrl(filepath: string): Promise<string> {
  if (filepath.startsWith("http://") || filepath.startsWith("https://")) {
    return filepath;
  }
  const params = getFetchParameters();
  const prefix = (params.pathPrefix || "").replace(/\/+$/, "");
  if (filepath.includes("://")) {
    try {
      const qp = new URLSearchParams({ cloud_path: filepath });
      const url = `${params.origin}${prefix}/signed-url?${qp}`;
      const res = await fetch(url, {
        headers: params.headers as Record<string, string>,
      });
      const data = await res.json();
      if (data.signed_url) return data.signed_url;
    } catch (e) {
      console.error("[MyPlugin] signed URL error:", e);
    }
    return filepath;
  }
  const path = `${prefix}/media`.replace(/\/\//g, "/");
  return `${params.origin}${path}?filepath=${encodeURIComponent(filepath)}`;
}

export default function MyModalPanel() {
  const dataOp = useOperatorExecutor(`${PLUGIN}/get_data`);
  const sampleOp = useOperatorExecutor(`${PLUGIN}/get_current_sample`);

  const [data, setData] = useState<string[]>([]);
  const [imgSrc, setImgSrc] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const hasTriggered = useRef(false);

  useEffect(() => {
    if (hasTriggered.current) return;
    hasTriggered.current = true;
    dataOp.execute({});
    sampleOp.execute({});
  }, []);

  useEffect(() => {
    if (dataOp.result?.values) {
      setData(dataOp.result.values);
      setLoading(false);
    }
  }, [dataOp.result]);

  useEffect(() => {
    if (sampleOp.result?.filepath) {
      resolveMediaUrl(sampleOp.result.filepath).then(setImgSrc);
    }
  }, [sampleOp.result]);

  useEffect(() => {
    if (dataOp.error) { console.error("[MyPlugin]", dataOp.error); setLoading(false); }
  }, [dataOp.error]);

  const refresh = useCallback(() => { sampleOp.execute({}); }, [sampleOp]);

  if (loading) return <div style={{ padding: 16, color: "#888" }}>Loading…</div>;
  return (
    <div style={{ padding: 16, color: "#e0e0e0" }}>
      <h3>My Modal Panel</h3>
      {imgSrc && <img src={imgSrc} alt="current" style={{ maxWidth: "100%" }} />}
      <button onClick={refresh}>Refresh Sample</button>
      <p>{data.length} items loaded</p>
    </div>
  );
}
```

### Modal panel troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Panel not in modal picker | `panelOptions` missing | Use `panelOptions: { surfaces: "modal" }` — NOT top-level `surfaces` |
| Panel not in modal picker | Name mismatch | `fiftyone.yml` `panels:` must exactly match `registerComponent` `name` |
| Panel not in modal picker | Bundle not loaded | Check `fiftyone.script` in `package.json`; verify `dist/index.umd.js` exists |
| "Unsupported View" error | `composite_view=True` | Don't use — switch to JS panel + Python operators |
| Data/dropdown empty | `.then()` on execute | Watch `executor.result` via `useEffect` instead |
| `AttributeError` on sample | Treating ID as Sample | `ctx.current_sample` is a string — use `ctx.dataset[ctx.current_sample]` |
| Images broken on Enterprise | Raw cloud paths (`gs://`) | Use `resolveMediaUrl()` with the `/signed-url` endpoint |
| Images broken locally | Wrong media URL | Use `getFetchParameters()` to build URL with correct origin/prefix |

---

## Debugging JavaScript Panels

### Browser DevTools

Open browser DevTools (F12) to debug JavaScript panels:

| Tab | Use For |
|-----|---------|
| **Console** | JS errors, syntax errors, plugin load failures, `console.log()` output |
| **Network** | API requests, payload data, response inspection |
| **Sources** | Breakpoints, step-through debugging |
| **React DevTools** | Component state, props inspection (install extension) |

### Debug Patterns

```typescript
// Debug component lifecycle
useEffect(() => {
  console.log("Panel mounted, data:", panelData);
  return () => console.log("Panel unmounted");
}, []);

// Debug state changes
useEffect(() => {
  console.log("State updated:", { samples, selectedField, isLoading });
}, [samples, selectedField, isLoading]);

// Debug API calls
const handleClick = async () => {
  console.log("Calling Python method with params:", params);
  const result = await client.my_method(params);
  console.log("Result received:", result);
};

// Debug Recoil state
const myState = useRecoilValue(myAtom);
console.log("Recoil state:", myState);
```

### Common Debug Scenarios

| Issue | Debug Approach |
|-------|----------------|
| Panel not loading | Check Console for syntax/import errors |
| Data not updating | Check Network tab for API response |
| Click not working | Add `console.log` in handler, check for errors |
| State not syncing | Log Recoil state, check Python trigger received |
| Build not reflecting changes | Run `npm run build`, hard refresh browser |

### Watch Mode Development

```bash
# Terminal 1: Watch TypeScript changes (auto-rebuilds)
cd my-plugin && npm run dev

# Terminal 2: Run FiftyOne server
python -m fiftyone.server.main

# After changes: Hard refresh browser (Ctrl+Shift+R)
```

---

## Troubleshooting

**Panel not appearing:**
- Check `name` in `registerComponent` matches `fiftyone.yml`
- Verify `dist/index.umd.js` was built
- Check browser console for JavaScript errors
- Refresh the FiftyOne App

**Build errors:**
- Ensure all peer dependencies are installed
- Check TypeScript errors in source files
- Verify Vite configuration

**State not updating:**
- Use `useRecoilValue` for reading state
- Use FiftyOne hooks like `useSetSelected` for writing
- Verify component re-renders when state changes

**Operator not found:**
- Register operators with `registerOperator`
- Add operator name to `fiftyone.yml` under `operators:`
- Restart FiftyOne App after changes

# Hybrid Plugin Development (Python + JavaScript)

## Contents
- [When to Use Hybrid](#when-to-use-hybrid)
- [Architecture Overview](#architecture-overview)
- [Plugin Structure](#plugin-structure)
- [Python Backend](#python-backend)
- [TypeScript Frontend](#typescript-frontend)
- [Communication Patterns](#communication-patterns)
- [TypeScript Operators](#typescript-operators)
- [Build Configuration](#build-configuration)
- [Complete Example](#complete-example)

---

## When to Use Hybrid

**Use hybrid plugins when you need:**
- Rich React UI with custom components
- Python backend for heavy computation or external APIs
- Real-time updates from Python to JavaScript
- Complex state synchronization between frontend and backend

**Use Python-only when:**
- Simple forms and basic UI
- Data processing without rich visualization
- Quick prototyping

**Use JavaScript-only when:**
- Pure UI enhancements
- Client-side logic only
- No backend processing needed

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                    FiftyOne App                      │
├─────────────────────┬───────────────────────────────┤
│   TypeScript/React  │         Python Backend         │
│   (Rich UI)         │    (Data Processing)           │
├─────────────────────┼───────────────────────────────┤
│ • Custom components │ • foo.Operator classes         │
│ • Recoil state      │ • foo.Panel classes            │
│ • Event handlers    │ • ctx.store() persistence      │
│ • usePanelEvent()   │ • ctx.trigger() communication  │
└─────────────────────┴───────────────────────────────┘
```

---

## Plugin Structure

```
my-hybrid-plugin/
├── fiftyone.yml           # Plugin manifest
├── __init__.py            # Python operators and panels
├── package.json           # Node.js dependencies
├── tsconfig.json          # TypeScript config
├── vite.config.ts         # Build config
├── src/
│   ├── index.ts           # Plugin entry point
│   ├── PluginView.tsx     # Main React component
│   ├── components/        # UI components
│   ├── hooks/             # Custom React hooks
│   ├── state/             # Recoil atoms
│   ├── operators.ts       # TypeScript operators (event handlers)
│   └── types.ts           # TypeScript interfaces
├── dist/
│   └── index.umd.js       # Built bundle (auto-generated)
└── requirements.txt       # Python dependencies
```

---

## Python Backend

### Panel with Custom View

```python
from fiftyone.operators.panel import Panel, PanelConfig
import fiftyone.operators.types as types

class MyHybridPanel(Panel):
    @property
    def config(self):
        return PanelConfig(
            name="my_hybrid_panel",
            label="My Hybrid Panel",
            icon="dashboard",
        )

    def on_load(self, ctx):
        # Initialize data for frontend
        ctx.panel.set_data("can_edit", True)
        ctx.panel.set_data("dataset_name", ctx.dataset.name)

    def render(self, ctx):
        return types.Property(
            types.Object(),
            view=types.View(
                component="PluginView",  # Matches React component name
                composite_view=True,
                # Expose Python methods to frontend
                process_data=self.process_data,
                get_status=self.get_status,
            ),
        )

    def process_data(self, ctx):
        """Called from frontend via usePanelEvent()"""
        params = ctx.params
        result = heavy_computation(params)
        ctx.panel.set_data("result", result)
        return {"success": True, "count": len(result)}

    def get_status(self, ctx):
        """Return current processing status"""
        store = ctx.store(f"my_plugin_{ctx.dataset._doc.id}")
        return {"status": store.get("status") or "idle"}
```

### Backend Operator with Store

```python
class ProcessingOperator(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="process_data",
            label="Process Data",
            allow_delegated_execution=True,
            execute_as_generator=True,
        )

    def execute(self, ctx):
        plugin_name = self.config.name.split("/")[-1]
        store = ctx.store(f"{plugin_name}_{ctx.dataset._doc.id}")

        total = len(ctx.target_view())
        for i, sample in enumerate(ctx.target_view()):
            # Process sample...
            store.set(f"sample_{sample.id}_status", "completed")

            # Send progress update to frontend
            yield ctx.trigger(
                "@myorg/my-plugin/progress_update",
                {"progress": (i + 1) / total, "sample_id": sample.id}
            )

        store.set("status", "completed")
        yield {"success": True, "total": total}
```

---

## TypeScript Frontend

### Custom View Component

```typescript
// src/PluginView.tsx
import React, { useEffect, useRef } from "react";
import { Box, Typography, Button, LinearProgress } from "@mui/material";
import { usePluginClient } from "./hooks/usePluginClient";
import { useRecoilState } from "recoil";
import { progressAtom } from "./state/progress";

export default function PluginView() {
  const client = usePluginClient();
  const [progress, setProgress] = useRecoilState(progressAtom);
  const hasLoadedRef = useRef(false);

  useEffect(() => {
    if (!hasLoadedRef.current) {
      hasLoadedRef.current = true;
      client.get_status().then((result) => {
        if (result?.result?.status) {
          setProgress((prev) => ({ ...prev, status: result.result.status }));
        }
      });
    }
  }, []);

  const handleProcess = async () => {
    setProgress({ status: "running", value: 0 });
    const result = await client.process_data({ option: "selected" });
    if (result?.result?.success) {
      setProgress({ status: "completed", value: 100 });
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h5">My Hybrid Plugin</Typography>

      {progress.status === "running" && (
        <LinearProgress variant="determinate" value={progress.value * 100} />
      )}

      <Button onClick={handleProcess} variant="contained">
        Process Data
      </Button>
    </Box>
  );
}
```

### State Management with Recoil

```typescript
// src/state/progress.ts
import { atom } from "recoil";

export interface ProgressState {
  status: "idle" | "running" | "completed" | "failed";
  value: number;
  message?: string;
}

export const progressAtom = atom<ProgressState>({
  key: "myPluginProgress",  // Unique key per plugin
  default: { status: "idle", value: 0 },
});
```

### Client Hook for Backend Communication

```typescript
// src/hooks/usePluginClient.ts
import { useCallback } from "react";
import { usePanelEvent } from "@fiftyone/operators";

export interface PluginClient {
  process_data: (params: { option: string }) => Promise<any>;
  get_status: () => Promise<any>;
}

export function usePluginClient(): PluginClient {
  const handleEvent = usePanelEvent();
  const pluginNamespace = "@myorg/my-plugin";  // Your plugin namespace

  return {
    process_data: useCallback(
      async (params) => {
        return new Promise((resolve, reject) => {
          handleEvent("process_data", {
            operator: `${pluginNamespace}/my_hybrid_panel#process_data`,
            params,
            callback: (result: any) => {
              result?.error ? reject(new Error(result.error)) : resolve(result);
            },
          });
        });
      },
      [handleEvent]
    ),

    get_status: useCallback(
      async () => {
        return new Promise((resolve, reject) => {
          handleEvent("get_status", {
            operator: `${pluginNamespace}/my_hybrid_panel#get_status`,
            params: {},
            callback: (result: any) => {
              result?.error ? reject(new Error(result.error)) : resolve(result);
            },
          });
        });
      },
      [handleEvent]
    ),
  };
}
```

---

## Communication Patterns

### Frontend → Backend

```typescript
// Call Python panel method
const result = await client.process_data({ option: "value" });

// Call Python operator
import { useOperatorExecutor } from "@fiftyone/operators";
const executor = useOperatorExecutor("@myorg/my-plugin/process_data");
await executor.execute({ param1: "value" });
```

### Backend → Frontend

```python
# Trigger TypeScript operator to update frontend state
ctx.trigger(
    "@myorg/my-plugin/progress_update",
    {"progress": 0.5, "message": "Processing..."}
)
```

### Real-time State Sync

```typescript
// TypeScript operator receives Python trigger and updates Recoil state
class ProgressUpdateOperator extends Operator {
  get config() {
    return new OperatorConfig({
      name: "progress_update",
      label: "Progress Update",
      unlisted: true,  // Hide from operator browser
    });
  }

  useHooks() {
    const setProgress = useSetRecoilState(progressAtom);
    return { setProgress };
  }

  async execute({ hooks, params }) {
    hooks.setProgress({
      status: "running",
      value: params.progress,
      message: params.message,
    });
  }
}
```

---

## TypeScript Operators

TypeScript operators act as **event handlers** for Python triggers:

```typescript
// src/operators.ts
import {
  Operator,
  OperatorConfig,
  registerOperator,
} from "@fiftyone/operators";
import { useSetRecoilState } from "recoil";
import { progressAtom } from "./state/progress";

class ProgressUpdateOperator extends Operator {
  get config() {
    return new OperatorConfig({
      name: "progress_update",
      label: "Progress Update",
      unlisted: true,  // Event handler, not user-facing
    });
  }

  useHooks() {
    const setProgress = useSetRecoilState(progressAtom);
    return { setProgress };
  }

  async execute({ hooks, params }) {
    const { progress, message, status } = params;
    hooks.setProgress((prev) => ({
      ...prev,
      value: progress ?? prev.value,
      message: message ?? prev.message,
      status: status ?? prev.status,
    }));
  }
}

// Register in src/index.ts
registerOperator(ProgressUpdateOperator, "@myorg/my-plugin");
```

---

## Build Configuration

### package.json

```json
{
  "name": "@myorg/my-hybrid-plugin",
  "version": "1.0.0",
  "type": "module",
  "main": "src/index.ts",
  "fiftyone": {
    "script": "dist/index.umd.js"
  },
  "scripts": {
    "dev": "vite build --watch",
    "build": "vite build"
  },
  "dependencies": {
    "@fiftyone/components": "*",
    "@fiftyone/operators": "*",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "recoil": "^0.7.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@vitejs/plugin-react": "^4.3.0",
    "@voxel51/fiftyone-js-plugin-build": "^2.0.0",
    "typescript": "^5.0.0",
    "vite": "^5.0.0"
  }
}
```

### vite.config.ts

```typescript
import { defineConfig } from "@voxel51/fiftyone-js-plugin-build";
import { dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));

export default defineConfig(__dirname, {
  buildConfigOverride: { sourcemap: true },
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

---

## Complete Example

### fiftyone.yml

```yaml
name: "@myorg/sample-processor"
version: "1.0.0"
description: "Process samples with real-time progress"
fiftyone:
  version: "*"
operators:
  - process_samples
panels:
  - processor_panel
```

### __init__.py

```python
import fiftyone.operators as foo
import fiftyone.operators.types as types
from fiftyone.operators.panel import Panel, PanelConfig

class ProcessorPanel(Panel):
    @property
    def config(self):
        return PanelConfig(
            name="processor_panel",
            label="Sample Processor",
            icon="play_arrow",
        )

    def on_load(self, ctx):
        store = ctx.store(f"processor_{ctx.dataset._doc.id}")
        ctx.panel.set_data("status", store.get("status") or "idle")

    def render(self, ctx):
        return types.Property(
            types.Object(),
            view=types.View(
                component="ProcessorView",
                composite_view=True,
                start_processing=self.start_processing,
            ),
        )

    def start_processing(self, ctx):
        # Trigger the background operator
        ctx.trigger("@myorg/sample-processor/process_samples", ctx.params)
        return {"started": True}


class ProcessSamplesOperator(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="process_samples",
            label="Process Samples",
            allow_delegated_execution=True,
            execute_as_generator=True,
        )

    def execute(self, ctx):
        view = ctx.target_view()
        total = len(view)

        for i, sample in enumerate(view):
            # Process sample...

            # Send progress to frontend
            yield ctx.trigger(
                "@myorg/sample-processor/update_progress",
                {"progress": (i + 1) / total}
            )

        yield {"success": True, "processed": total}


def register(p):
    p.register(ProcessorPanel)
    p.register(ProcessSamplesOperator)
```

### src/index.ts

```typescript
import { registerComponent, PluginComponentType } from "@fiftyone/plugins";
import { registerOperator } from "@fiftyone/operators";
import ProcessorView from "./ProcessorView";
import { UpdateProgressOperator } from "./operators";

// Register React component
registerComponent({
  name: "ProcessorView",
  component: ProcessorView,
  type: PluginComponentType.Panel,
});

// Register event handler operator
registerOperator(UpdateProgressOperator, "@myorg/sample-processor");
```

### Development Workflow

```bash
# Terminal 1: Watch TypeScript changes
cd my-hybrid-plugin && npm run dev

# Terminal 2: Launch FiftyOne App
python -c "import fiftyone as fo; fo.launch_app()"
```

Changes to TypeScript files auto-rebuild. Refresh the FiftyOne App to see updates.

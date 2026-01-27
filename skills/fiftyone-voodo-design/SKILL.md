---
name: fiftyone-voodo-design
description: Build FiftyOne UIs using VOODO (Voxel Official Design Ontology), the official React component library. Use when building plugin panels, creating interactive UIs, or styling FiftyOne applications. Fetches current documentation dynamically from llms.txt.
---

# VOODO Design System for FiftyOne

VOODO is the official React component library for FiftyOne applications.

**Documentation is fetched dynamically** - always get current components from llms.txt before writing code.

## Key Directive

**ALWAYS fetch llms.txt BEFORE writing any UI code:**

```
WebFetch(
    url="https://voodo.dev.fiftyone.ai/llms.txt",
    prompt="List all available VOODO components with their variants and use cases"
)
```

This gives you:
- All current components (buttons, inputs, toasts, etc.)
- Available variants for each component
- Design token categories (colors, spacing, typography)
- Links to interactive Storybook docs

## Workflow

### 1. Fetch component list

```
WebFetch(
    url="https://voodo.dev.fiftyone.ai/llms.txt",
    prompt="What VOODO components are available for building forms?"
)
```

### 2. Use components from the fetched list

```typescript
// Import only components that exist in llms.txt
import { Button, Input, Select } from "@voxel51/voodo";
```

### 3. For detailed props, direct user to Storybook

The llms.txt includes Storybook links for each component. For detailed prop documentation:

```
"For Button props and examples, see: https://voodo.dev.fiftyone.ai/?path=/docs/components-button--docs"
```

**Note**: Storybook is a JavaScript app - WebFetch cannot extract its content. Direct users to browse interactively.

## Installation

```json
{
  "dependencies": {
    "@voxel51/voodo": "latest"
  }
}
```

## FiftyOne Patterns

- **Dark theme**: FiftyOne App uses dark mode by default
- **Semantic variants**: Use success/danger/warning for actions (verify names from llms.txt)
- **Design tokens**: Use spacing/color tokens instead of arbitrary values

## Integration with FiftyOne SDK

```typescript
import { useRecoilValue } from "recoil";
import * as fos from "@fiftyone/state";  // Standard FiftyOne alias
import { Button, Text, Stack } from "@voxel51/voodo";

const MyPanel: React.FC = () => {
  const dataset = useRecoilValue(fos.dataset);
  return (
    <Stack>
      <Text>{dataset?.name}</Text>
      <Button>Process</Button>
    </Stack>
  );
};
```

## Resources

| Resource | URL |
|----------|-----|
| **llms.txt** (fetch first) | https://voodo.dev.fiftyone.ai/llms.txt |
| **Interactive Storybook** | https://voodo.dev.fiftyone.ai/ |
| **npm package** | `@voxel51/voodo` |

**Related**: Use `fiftyone-develop-plugin` skill for full plugin setup.

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Component not found | Fetch llms.txt to verify current name |
| Props not working | Direct user to Storybook for current API |
| Styles not applying | Test in dark mode, use design tokens |

---
name: fiftyone-voodo-design
description: Build FiftyOne UIs using VOODO (@voxel51/voodo), the official React component library. Use when building plugin panels, creating interactive UIs, or styling FiftyOne applications. Fetches complete component API reference dynamically.
---

# VOODO Design System for FiftyOne

VOODO (`@voxel51/voodo`) is the official React component library for FiftyOne applications. Source: https://github.com/voxel51/design-system

## Key Directive

**ALWAYS fetch the LLM reference BEFORE writing any UI code:**

```
WebFetch(
    url="https://voodo.dev.fiftyone.ai/voodo-llm-reference.md",
    prompt="Read the complete VOODO component API, design tokens, and composition patterns"
)
```

This gives you:
- All design token enums with exact member values (Size, Spacing, Variant, Orientation, etc.)
- Every component's props, types, defaults, and usage examples
- Composition patterns for common layouts (forms, cards, lists, selects)
- Anti-patterns to avoid (e.g. raw Tailwind vs. component props)

## Workflow

### 1. Fetch the reference

```
WebFetch(
    url="https://voodo.dev.fiftyone.ai/voodo-llm-reference.md",
    prompt="What VOODO components and tokens are available for building [describe UI]?"
)
```

### 2. Use components and design tokens from the reference

Always import from `@voxel51/voodo`. Always use enum values — never pass raw strings.

```typescript
import { Button, Input, Stack, Text, FormField } from "@voxel51/voodo";
import { Orientation, Size, Spacing, Variant, TextColor } from "@voxel51/voodo";
```

### 3. Follow composition patterns

The reference includes patterns for:
- **Forms**: Wrap controls in `<FormField>`, group with `<FormFieldGroup>`
- **Layout**: Use `<Stack>` with `orientation`, `spacing`, `align`, `justify` props — not Tailwind flex classes
- **Cards**: Use `<Card>` / `<RichCard>` for contained content
- **Lists**: Use `Descriptor<T>[]` pattern with `<RichList>` or `<RichButtonGroup>`
- **Feedback**: Use `<Toast>`, `<Tooltip>`, `<EmptyState>`

## Installation

```json
{
  "dependencies": {
    "@voxel51/voodo": "latest"
  }
}
```

Import the theme CSS in your app entry point:

```typescript
import "@voxel51/voodo/theme.css";
```

## FiftyOne Patterns

- **Dark theme**: FiftyOne App uses dark mode by default
- **Semantic variants**: Use `Variant.Success`, `Variant.Danger`, `Variant.Secondary` for actions
- **Design tokens**: Always use enum values (`Spacing.Md`, `Size.Sm`) — never arbitrary CSS values
- **Layout**: Use `<Stack>` with `align` and `justify` props instead of Tailwind `items-*` / `justify-*` classes

## Integration with FiftyOne SDK

```typescript
import { useRecoilValue } from "recoil";
import * as fos from "@fiftyone/state";  // Standard FiftyOne alias
import { Button, Text, Stack, FormField, Input } from "@voxel51/voodo";
import { Orientation, Spacing, Size, Variant, TextColor } from "@voxel51/voodo";

const MyPanel: React.FC = () => {
  const dataset = useRecoilValue(fos.dataset);
  return (
    <Stack orientation={Orientation.Column} spacing={Spacing.Md}>
      <Text color={TextColor.Secondary}>{dataset?.name}</Text>
      <FormField
        label="Filter"
        control={<Input size={Size.Sm} placeholder="Search..." />}
      />
      <Button variant={Variant.Primary} size={Size.Sm}>
        Process
      </Button>
    </Stack>
  );
};
```

## Resources

| Resource | URL |
|----------|-----|
| **LLM Reference** (fetch first) | https://voodo.dev.fiftyone.ai/voodo-llm-reference.md |
| **Source repo** | https://github.com/voxel51/design-system |
| **Interactive Storybook** | https://voodo.dev.fiftyone.ai/ |
| **npm package** | `@voxel51/voodo` |

**Related**: Use `fiftyone-develop-plugin` skill for full plugin setup.

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Component not found | Fetch the LLM reference to verify current component name |
| Wrong prop value | Use enum members (e.g. `Size.Md`), not strings (e.g. `"md"`) |
| Layout not working | Use `<Stack>` with `orientation`, `spacing`, `align`, `justify` props |
| Styles not applying | Ensure `@voxel51/voodo/theme.css` is imported; test in dark mode |

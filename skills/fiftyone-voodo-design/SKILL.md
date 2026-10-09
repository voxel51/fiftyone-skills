---
name: fiftyone-voodo-design
description: Build FiftyOne UIs using VOODO (@voxel51/voodo), the official React component library. Use when building plugin panels, creating interactive UIs, styling FiftyOne applications, or choosing components, text sizes, colors, and spacing. Looks up the installed version's components and token values with `npx @voxel51/voodo` before writing code.
---

# VOODO Design System for FiftyOne

VOODO (`@voxel51/voodo`) is the official React component library for FiftyOne applications. Source: https://github.com/voxel51/design-system. Storybook: https://voodo.dev.fiftyone.ai

## Key Directive

**Look up components in the installed package BEFORE writing any UI code.** VOODO ships its own docs command, which reads the version your project installed:

```bash
npx @voxel51/voodo list             # every component, one line each
npx @voxel51/voodo docs Button      # one component's props, docs, and allowed token values
npx @voxel51/voodo tokens Spacing   # one token group's values (all groups with no argument)
npx @voxel51/voodo icons            # every icon component name
```

Run it from the project that depends on `@voxel51/voodo` (2.1.0 or later). Don't guess component names or prop values: `docs` prints the exact strings each prop accepts.

## Rules

The docs say what exists. These rules say how to use it:

1. **Token props take plain strings**: `variant="primary"`, `size="sm"`, `spacing="md"`. The const members (`Size.Sm`) still compile but are the older style.
2. **Compose before you build.** Check `npx @voxel51/voodo list` before hand-rolling anything. Mid-level patterns usually exist: `FormField`, `RichList`, `EmptyState`, `Toolbar`, `Modal`.
3. **Layout with `<Stack>`** (`orientation="row"` or `"col"`, `spacing`, `align`, `justify`), not Tailwind flex classes.
4. **Text with `<Text variant=…>` roles**: `body-primary` (15px, the default), `body-secondary` (14px), `body-tertiary` (12px), `heading-xs` … `heading-xl`, `label`, `caption`, `code-primary`. The size-only variants (`"xs"` … `"xxl"`) are deprecated. Pick the role by size; don't reshape `Text` with font, leading, or `style` overrides.
5. **Colors are tokens**: pass them as props (`color="text-secondary"`). Outside VOODO components, use the exported helpers `bgColorClass`, `textColorClass`, `borderColorClass`, or `getColorCssVar`. Never a hand-written `var(--color-…)` or a raw hex.
6. **Data colors**: `viz-chart-*` for charts and other UI; `viz-overlay-*` for labels drawn over images and video.
7. **Icons are components**: `<CheckIcon />`, `<EditIcon />` (`npx @voxel51/voodo icons`). `<Icon name=…>` is deprecated.
8. **Check both themes.** The FiftyOne App defaults to dark mode, but surfaces differ in light mode (`bg-card-elevated` is white there).

## Common jobs

| Job | Components |
|-----|------------|
| Panel layout | `Stack`, `Card`, `Divider` |
| Headings and text | `Heading` (`level="h1"` … `"h4"`), `Text` |
| Actions | `Button`, `IconAction`, `TextAction`, `Dropdown` / `ContextMenu` with the `Menu*` items |
| Forms | `FormField` around `Input`, `Select`, `Combobox`, `Checkbox`, `RadioGroup`, `Toggle`, `TextArea`, `DatePicker`, sliders; `FormFieldGroup` |
| Lists and tables | `RichList`, `Table` (+ `TableHeader`, `TableRow`, `TableCell`, …), `TreeView`, `ImageList` |
| Overlays | `Modal`, `Sheet`, `Drawer`, `Popover`, `Tooltip` |
| Feedback | `Toast` / `ToastContainer`, `Progress`, `Loader` (`type="spinner"` or `"bars"` for AI work), `LoadingDots`, `StatusDot`, `EmptyState` |
| Tabs and steps | `Tabs` / `Tab`, `ToggleSwitch`, `StepRail` |
| Files | `Dropzone`, `UploadList` |

Run `npx @voxel51/voodo docs <Name>` for each before using it.

## Getting started

1. **Install** it in your plugin or app:
   ```json
   {
     "dependencies": {
       "@voxel51/voodo": "^2.1.0"
     }
   }
   ```
2. **Import the theme CSS once** in your entry point. Every component relies on its CSS variables:
   ```typescript
   import "@voxel51/voodo/theme.css";
   ```
3. **Render a first component.** Everything imports from `@voxel51/voodo`; see the panel below.
4. **Read a component's docs** with `npx @voxel51/voodo docs <Name>`. It prints the component's TypeScript props with their docs, then the allowed values for every token type those props use:
   ```
   // Token values used above
   type ButtonSize = "xs" | "sm" | "md";
   type Variant = "primary" | "secondary" | "success" | "danger" | "icon" | "borderless" | "expressive";
   ```
   Pass those strings as props. A `// deprecated:` comment lists values that still work but don't belong in new code.

### A first panel

```tsx
import { useState } from "react";
import { useRecoilValue } from "recoil";
import * as fos from "@fiftyone/state"; // Standard FiftyOne alias
import { Button, FormField, Input, Stack, Text } from "@voxel51/voodo";

const MyPanel: React.FC = () => {
  const dataset = useRecoilValue(fos.dataset);
  const [query, setQuery] = useState("");

  return (
    <Stack orientation="col" spacing="md">
      <Text variant="body-secondary" color="text-secondary">
        {dataset?.name}
      </Text>
      <FormField
        label="Filter"
        control={
          <Input
            size="sm"
            placeholder="Search..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        }
      />
      <Button variant="primary" size="sm" onClick={() => runSearch(query)}>
        Process
      </Button>
    </Stack>
  );
};
```

## Patterns

These follow the shapes of FiftyOne's own similarity-search panel, written in the current style.

### Panel header with actions

```tsx
import {
  AddIcon,
  Button,
  Heading,
  IconAction,
  RefreshIcon,
  Stack,
  Tooltip,
} from "@voxel51/voodo";

<Stack orientation="row" align="center" justify="between">
  <Heading level="h2">Searches</Heading>
  <Stack orientation="row" spacing="sm" align="center">
    <Tooltip content="Refresh">
      <IconAction icon={RefreshIcon} aria-label="Refresh" onClick={onRefresh} />
    </Tooltip>
    <Button variant="primary" size="sm" leadingIcon={AddIcon} onClick={onNew}>
      New search
    </Button>
  </Stack>
</Stack>;
```

Icon-only buttons are `IconAction`, always with an `aria-label`.

### List with an empty state

```tsx
import {
  DeleteIcon,
  EmptyState,
  IconAction,
  RichList,
  SearchIcon,
  Stack,
  Text,
} from "@voxel51/voodo";

const items = runs.map((run) => ({
  id: run.id,
  data: {
    primaryContent: (
      <Stack orientation="col" spacing="xs">
        <Text variant="body-primary">{run.name}</Text>
        <Text variant="body-tertiary" color="text-secondary">
          {run.summary}
        </Text>
      </Stack>
    ),
    actions: (
      <IconAction
        icon={DeleteIcon}
        aria-label="Delete"
        onClick={() => onDelete(run.id)}
      />
    ),
  },
}));

return runs.length === 0 ? (
  <EmptyState
    icon={SearchIcon}
    title="No searches yet"
    description="Start a new search to find similar samples."
  />
) : (
  <RichList listItems={items} />
);
```

`RichList` takes descriptors: `{ id, data }`, where `data` holds the row's props. Use `EmptyState`, not a centered stack of text.

### Form

```tsx
import {
  Button,
  FormField,
  Input,
  RadioGroup,
  Select,
  Stack,
} from "@voxel51/voodo";

const indexOptions = indexes.map((key) => ({ id: key, data: { label: key } }));

<Stack orientation="col" spacing="lg">
  <FormField
    label="Similarity index"
    control={
      <Select
        exclusive
        options={indexOptions}
        value={index}
        onChange={(next) => setIndex(typeof next === "string" ? next : undefined)}
      />
    }
  />
  <FormField
    label="Target"
    control={
      <RadioGroup
        options={[
          { value: "dataset", label: "Full dataset" },
          { value: "view", label: "Current view" },
        ]}
        value={target}
        onChange={setTarget}
      />
    }
  />
  <FormField
    label="Max results"
    description="How many similar samples to return."
    control={
      <Input type="number" value={k} onChange={(e) => setK(e.target.value)} />
    }
  />
  <Stack orientation="row" spacing="sm" justify="end">
    <Button variant="secondary" onClick={onCancel}>
      Cancel
    </Button>
    <Button variant="primary" onClick={onSubmit} disabled={!index}>
      Search
    </Button>
  </Stack>
</Stack>;
```

Wrap every control in `FormField` for its label, description, and error.

## Resources

| Resource | Where |
|----------|-------|
| **Component docs** (use first) | `npx @voxel51/voodo docs <Name>` in your project |
| **Interactive Storybook** | https://voodo.dev.fiftyone.ai/ |
| **Source repo** | https://github.com/voxel51/design-system |
| **npm package** | `@voxel51/voodo` |

**Related**: Use `fiftyone-develop-plugin` skill for full plugin setup.

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Component not found | `npx @voxel51/voodo list`; names change between versions |
| Wrong prop value | `npx @voxel51/voodo docs <Name>` lists the strings each prop accepts |
| Text looks too small or too large | Use a role variant (`body-secondary`, …), not a size-only one (`"sm"`) |
| Layout not working | Use `<Stack>` with `orientation`, `spacing`, `align`, `justify` props |
| Styles not applying | Ensure `@voxel51/voodo/theme.css` is imported; check dark and light mode |

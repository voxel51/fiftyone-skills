# VOODO Design

Build FiftyOne plugin UIs using VOODO (`@voxel51/voodo`), the official React component library.

## Install

```bash
curl -sL skil.sh | sh -s -- voxel51/fiftyone-skills
```

When prompted, select **fiftyone-voodo-design** from the menu.

## Requirements

- [FiftyOne](https://docs.voxel51.com/getting_started/install.html)
- Node.js 18+
- Familiarity with React and FiftyOne plugin development

## Usage

Ask your AI assistant:

```
"Build a panel that shows a bar chart of class distributions using VOODO"
"Create a settings form for my plugin using VOODO components"
"Style this plugin panel to match the FiftyOne design system"
```

Before writing any code, the skill looks up components and token values in your installed VOODO version with `npx @voxel51/voodo` (2.1.0 or later), so it uses props and values that exist in that version.

## Example

```
"Create a FiftyOne panel with a search input and a scrollable list of results using VOODO"
```

The skill will generate a React component using VOODO's `Input`, `RichList`, and `Stack` components with the correct design tokens.

## See also

- [VOODO documentation](https://voodo.dev.fiftyone.ai)
- [Plugin development docs](https://docs.voxel51.com/plugins/developing_plugins.html)

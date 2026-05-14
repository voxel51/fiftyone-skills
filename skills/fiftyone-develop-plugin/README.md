# Develop Plugin

Scaffold and implement custom FiftyOne plugins: operators, panels, and JavaScript components.

## Install

```bash
curl -sL skil.sh | sh -s -- voxel51/fiftyone-skills
```

When prompted, select **fiftyone-develop-plugin** from the menu.

## Requirements

- [FiftyOne](https://docs.voxel51.com/getting_started/install.html)
- Python 3.8+

## Usage

Ask your AI assistant:

```
"Create a FiftyOne operator that filters samples by confidence score"
"Build a panel that shows a class distribution chart"
"Scaffold a plugin that integrates with my annotation tool"
```

The skill asks clarifying questions, presents the file structure and design for your approval, then generates the full plugin code with tests.

## Example output

```
my-plugin/
├── fiftyone.yml
├── __init__.py        # operator/panel definitions
└── README.md
```

Install the generated plugin:

```bash
fiftyone plugins create my-plugin
```

## See also

- [Plugin development docs](https://docs.voxel51.com/plugins/developing_plugins.html)
- [FiftyOne Plugins](https://github.com/voxel51/fiftyone-plugins)

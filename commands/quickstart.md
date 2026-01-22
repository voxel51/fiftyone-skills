---
description: Guided quickstart for FiftyOne - choose between user workflows (import, inference, visualization) or developer workflows (plugin development)
---

# FiftyOne Quickstart

Welcome to FiftyOne! This quickstart will guide you through your first workflow.

## Prerequisites Check

First, let me verify your setup by listing available datasets:

Use the `list_datasets` MCP tool to check the connection.

If this fails, run:
```bash
pip install fiftyone-mcp-server
```

Then check `/fiftyone:help` for environment configuration.

---

## Choose Your Path

### Option 1: User Quickstart

Build and explore a computer vision dataset.

**Step 1: Load a Dataset**

You can either:

- **Use the quickstart dataset** (built-in):
  ```
  Load the FiftyOne quickstart dataset
  ```

- **Import your own dataset**:
  ```
  Use /fiftyone:fiftyone-dataset-import to import my dataset from /path/to/data
  ```

**Step 2: Run Model Inference**

Apply a model to your dataset:

```
Use /fiftyone:fiftyone-dataset-inference to run object detection on my dataset
```

This will run a Zoo model (like YOLO or Faster R-CNN) and add predictions to your samples.

**Step 3: Explore in the App**

Launch the FiftyOne App to visualize your data and predictions:

```
Launch the FiftyOne App with my dataset
```

From here you can:
- Browse samples and labels
- Filter by predictions or ground truth
- Identify model errors

**Next Steps**

Once you're comfortable, try:
- `/fiftyone:fiftyone-find-duplicates` - Clean your dataset
- `/fiftyone:fiftyone-model-evaluation` - Evaluate prediction quality
- `/fiftyone:fiftyone-embeddings-visualization` - Explore data distribution

---

### Option 2: Developer Quickstart

Create a custom FiftyOne plugin.

**Step 1: Start Plugin Development**

```
Use /fiftyone:fiftyone-develop-plugin to create a new plugin
```

The skill will guide you through:
1. Defining your plugin's purpose
2. Choosing between operators (actions) or panels (UI)
3. Generating the plugin structure
4. Installing and testing locally

**Step 2: Follow the Guided Workflow**

The develop-plugin skill provides comprehensive guidance on:
- Plugin directory structure
- Python operator patterns
- JavaScript/React panels
- Hybrid plugins with Python backend + JS frontend
- Testing and debugging

**Next Steps**

For code contributions:
- `/fiftyone:fiftyone-code-style` - Follow FiftyOne conventions
- [FiftyOne Plugins Repository](https://github.com/voxel51/fiftyone-plugins) - Browse examples

---

## Need Help?

- `/fiftyone:help` - Full documentation of all skills
- [FiftyOne Docs](https://docs.voxel51.com/)
- [Discord Community](https://discord.gg/fiftyone-community)

---
description: Get help with FiftyOne skills, understand available workflows, and troubleshoot setup issues
---

# FiftyOne Skills Help

This plugin provides expert workflows for building high-quality datasets and computer vision models using [FiftyOne](https://docs.voxel51.com/).

## When to Use This Help

- First time using FiftyOne skills
- Encountering setup or configuration issues
- Want to understand what skills are available

## Prerequisites

Before using FiftyOne skills, ensure the MCP server is installed:

```bash
pip install fiftyone-mcp-server
```

The plugin automatically configures the MCP server connection via `.mcp.json`. If you installed FiftyOne in a virtual environment or conda environment, update the command path in `.mcp.json` to point to your environment's executable:

```json
{
  "mcpServers": {
    "fiftyone": {
      "command": "/path/to/your/venv/bin/fiftyone-mcp"
    }
  }
}
```

## Available Skills

### FiftyOne Use

Skills for working with datasets and models:

| Skill | Command | Use When |
|-------|---------|----------|
| **Dataset Import** | `/fiftyone:fiftyone-dataset-import` | Importing any dataset (COCO, YOLO, VOC, videos, point clouds, multimodal) |
| **Dataset Export** | `/fiftyone:fiftyone-dataset-export` | Exporting datasets to standard formats for training or sharing |
| **Find Duplicates** | `/fiftyone:fiftyone-find-duplicates` | Removing duplicate or near-duplicate images from datasets |
| **Dataset Inference** | `/fiftyone:fiftyone-dataset-inference` | Running detection, classification, segmentation, or embeddings on data |
| **Model Evaluation** | `/fiftyone:fiftyone-model-evaluation` | Computing mAP, precision, recall, confusion matrices |
| **Embeddings Visualization** | `/fiftyone:fiftyone-embeddings-visualization` | Exploring dataset structure, finding clusters, identifying outliers |

### FiftyOne Develop

Skills for developers building with FiftyOne:

| Skill | Command | Use When |
|-------|---------|----------|
| **Develop Plugin** | `/fiftyone:fiftyone-develop-plugin` | Creating custom operators or panels for FiftyOne App |
| **Code Style** | `/fiftyone:fiftyone-code-style` | Writing Python code following FiftyOne conventions |
| **Issue Triage** | `/fiftyone:fiftyone-issue-triage` | Triaging GitHub issues in the FiftyOne repository |

## Troubleshooting Checklist

If skills aren't working as expected:

1. **Verify MCP server installation**
   ```bash
   pip show fiftyone-mcp-server
   ```

2. **Test MCP connection**
   Ask: "List my FiftyOne datasets"

   If this works, MCP is properly configured.

3. **Check FiftyOne installation**
   ```bash
   pip show fiftyone
   ```

4. **Verify Python environment**
   Ensure you're using the same environment where FiftyOne is installed.

## Quick Commands

- `/fiftyone:quickstart` - Guided workflow to get started
- `/fiftyone:help` - This help document

## Resources

- [FiftyOne Documentation](https://docs.voxel51.com/)
- [FiftyOne MCP Server](https://github.com/voxel51/fiftyone-mcp-server)
- [FiftyOne Plugins](https://github.com/voxel51/fiftyone-plugins)
- [Discord Community](https://discord.gg/fiftyone-community)
- [GitHub Issues](https://github.com/voxel51/fiftyone-skills/issues)

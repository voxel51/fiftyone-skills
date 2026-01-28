# FiftyOne Skills

<div align="center">
<p align="center">

<!-- prettier-ignore -->
<img src="https://user-images.githubusercontent.com/25985824/106288517-2422e000-6216-11eb-871d-26ad2e7b1e59.png" height="55px"> &nbsp;
<img src="https://user-images.githubusercontent.com/25985824/106288518-24bb7680-6216-11eb-8f10-60052c519586.png" height="50px">

</p>

**Expert workflows for computer vision powered by AI assistants**

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![FiftyOne](https://img.shields.io/badge/FiftyOne-v1.10+-orange.svg)](https://github.com/voxel51/fiftyone)
[![MCP Server](https://img.shields.io/badge/MCP%20Server-fiftyone--mcp-green.svg)](https://github.com/voxel51/fiftyone-mcp-server)
[![Discord](https://img.shields.io/badge/Discord-FiftyOne%20Community-7289DA.svg)](https://discord.gg/fiftyone-community)

[Documentation](https://docs.voxel51.com) · [MCP Server](https://github.com/voxel51/fiftyone-mcp-server) · [FiftyOne Plugins](https://github.com/voxel51/fiftyone-plugins) · [Discord](https://discord.gg/fiftyone-community)

</div>

## What are Skills?

Skills are packaged workflows that teach AI assistants to perform complex computer vision tasks autonomously. Combined with the [FiftyOne MCP Server](https://github.com/voxel51/fiftyone-mcp-server), you can find duplicates, run inference, and explore datasets using natural language.

```
"Find and remove duplicate images from my dataset"
"Import this COCO dataset and run object detection"
"Visualize my embeddings and identify outliers"
```

Skills bridge the gap between natural language and FiftyOne's 80+ operators, providing step-by-step guidance that AI assistants follow to complete complex workflows.


## Available Skills

| Skill | Description |
|-------|-------------|
| 📥 [**Dataset Import**](skills/fiftyone-dataset-import/SKILL.md) | Universal import for all media types, label formats, multimodal groups, and Hugging Face Hub |
| 📤 [**Dataset Export**](skills/fiftyone-dataset-export/SKILL.md) | Export datasets to COCO, YOLO, VOC, CVAT, CSV, Hugging Face Hub, and more |
| 🔍 [**Find Duplicates**](skills/fiftyone-find-duplicates/SKILL.md) | Find and remove duplicate images using brain similarity |
| 🤖 [**Dataset Inference**](skills/fiftyone-dataset-inference/SKILL.md) | Run Zoo models for detection, classification, segmentation, embeddings |
| 📈 [**Model Evaluation**](skills/fiftyone-model-evaluation/SKILL.md) | Compute mAP, precision, recall, confusion matrices, analyze TP/FP/FN |
| 📊 [**Embeddings Visualization**](skills/fiftyone-embeddings-visualization/SKILL.md) | Visualize datasets in 2D, find clusters, identify outliers |
| 🔌 [**Develop Plugin**](skills/fiftyone-develop-plugin/SKILL.md) | Create custom FiftyOne plugins (operators and panels) |
| 🎨 [**VOODO Design**](skills/fiftyone-voodo-design/SKILL.md) | Build UIs with VOODO React components and design tokens |
| 📝 [**Code Style**](skills/fiftyone-code-style/SKILL.md) | Write Python code following FiftyOne's official conventions |
| 🏷️ [**Issue Triage**](skills/fiftyone-issue-triage/SKILL.md) | Triage GitHub issues: validate status, categorize, generate responses |

## Quick Start

### Step 1: Install the MCP Server

```bash
pip install fiftyone-mcp-server
```

> **⚠️ Important:** Make sure to use the same Python environment where you installed the MCP server when configuring your AI tool. If you installed it in a virtual environment or conda environment, you must activate that environment or specify the full path to the executable.

### Step 2: Configure Your AI Tool

<details>
<summary><b>Claude Code</b> (Recommended)</summary>

```bash
claude mcp add fiftyone -- fiftyone-mcp
```

</details>

<details>
<summary><b>Claude Desktop</b></summary>

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "fiftyone": {
      "command": "fiftyone-mcp"
    }
  }
}
```

</details>

<details>
<summary><b>Cursor</b></summary>

[![Install in Cursor](https://cursor.com/deeplink/mcp-install-dark.svg)](cursor://anysphere.cursor-deeplink/mcp/install?name=fiftyone&config=eyJjb21tYW5kIjoiZmlmdHlvbmUtbWNwIn0)

Add to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "fiftyone": {
      "command": "fiftyone-mcp"
    }
  }
}
```

</details>

<details>
<summary><b>VSCode</b></summary>

[![Install in VS Code](https://img.shields.io/badge/VS_Code-Install_Server-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect/mcp/install?name=fiftyone&config=%7B%22command%22%3A%22fiftyone-mcp%22%7D)

Add to `.vscode/mcp.json`:

```json
{
  "servers": {
    "fiftyone": {
      "command": "fiftyone-mcp"
    }
  }
}
```

</details>

### Step 3: Install Skills

**Universal Installer** (Recommended):
```bash
curl -sL skil.sh | sh -s -- voxel51/fiftyone-skills
```
Interactive prompts let you select skills, agents, and install scope (project or global).

Supported agents: Claude Code, Cursor, Codex, OpenCode, GitHub Copilot, Amp, Antigravity, Roo Code, Kilo Code, Goose

**Claude Code:**
```bash
# Register the skills marketplace
/plugin marketplace add voxel51/fiftyone-skills

# Install a skill
/plugin install fiftyone-find-duplicates@fiftyone-skills
```

**Codex:**
```bash
codex --ask-for-approval never "Summarize the current instructions."
```

**Gemini CLI:**
```bash
gemini extensions install https://github.com/voxel51/fiftyone-skills.git --consent
```

### Step 4: Use It

```
Use the FiftyOne find duplicates skill to remove redundant images from my quickstart dataset
```

Claude will automatically load the skill instructions and execute the full workflow.

## Skill Structure

Each skill follows the [Agent Skills](https://agentskills.io) specification:

```
skills/
└── fiftyone-find-duplicates/
    └── SKILL.md                     # Instructions for AI
```

**SKILL.md format:**

```markdown
---
name: skill-name
description: When to use this skill
---

# Overview
What this skill does

# Prerequisites
Required setup

# Key Directives
ALWAYS/NEVER rules for AI

# Workflow
Step-by-step instructions

# Troubleshooting
Common errors and solutions
```

## Contributing

We welcome contributions! Here's how to create a new skill:

1. **Fork** this repository
2. **Copy** an existing skill folder (e.g., `skills/fiftyone-find-duplicates/`)
3. **Update** `SKILL.md` with your workflow
4. **Add** your skill to `.claude-plugin/marketplace.json`
5. **Test** with your AI assistant
6. **Submit** a Pull Request

See [find-duplicates SKILL.md](skills/fiftyone-find-duplicates/SKILL.md) for a complete example.

## Resources

| Resource | Description |
|----------|-------------|
| [FiftyOne Docs](https://docs.voxel51.com) | Official documentation |
| [FiftyOne MCP Server](https://github.com/voxel51/fiftyone-mcp-server) | MCP server for AI integration |
| [FiftyOne Plugins](https://github.com/voxel51/fiftyone-plugins) | Official plugin collection |
| [Agent Skills Spec](https://agentskills.io) | Skills format specification |
| [PyPI Package](https://pypi.org/project/fiftyone-mcp-server/) | MCP server on PyPI |
| [Discord Community](https://discord.gg/fiftyone-community) | Get help and share ideas |

## 🧡 Community

Join the FiftyOne community to get help, share your skills, and connect with other users:

- **Discord**: [FiftyOne Community](https://discord.gg/fiftyone-community)
- **GitHub Issues**: [Report bugs or request features](https://github.com/voxel51/fiftyone-skills/issues)

---

<div align="center">

Copyright 2017-2026, Voxel51, Inc. · [Apache 2.0 License](LICENSE)

</div>

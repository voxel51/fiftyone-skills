# FiftyOne Skills

<div align="center">
<p align="center">

<!-- prettier-ignore -->
<img src="https://user-images.githubusercontent.com/25985824/106288517-2422e000-6216-11eb-871d-26ad2e7b1e59.png" height="55px"> &nbsp;
<img src="https://user-images.githubusercontent.com/25985824/106288518-24bb7680-6216-11eb-8f10-60052c519586.png" height="50px">

</p>
</div>

> Expert workflows for FiftyOne datasets powered by AI assistants

## Overview

Skills are packaged workflows that teach AI assistants to perform complex computer vision tasks autonomously. Combined with the [FiftyOne MCP Server](https://github.com/AdonaiVera/fiftyone-mcp-server), you can find duplicates, run inference, and explore datasets using natural language.

## Available Skills

| Skill | Description |
|-------|-------------|
| [**Find Duplicates**](find-duplicates/skills/fiftyone-find-duplicates/SKILL.md) | Find and remove duplicate images using brain similarity |
| [**Dataset Inference**](dataset-inference/skills/fiftyone-dataset-inference/SKILL.md) | Import datasets (COCO, YOLO, VOC) and run model inference |

## Quick Start

### Step 1: Install the MCP Server

```bash
pip install fiftyone-mcp-server
```

### Step 2: Configure Your AI Tool

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
<summary><b>Claude Code</b></summary>

```bash
claude mcp add fiftyone -- fiftyone-mcp
```
</details>

<details>
<summary><b>Cursor</b></summary>

Add to Cursor MCP settings:

```json
{
  "fiftyone": {
    "command": "fiftyone-mcp"
  }
}
```
</details>

<details>
<summary><b>VSCode</b></summary>

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

### Step 3: Install Skills (Claude Code)

```bash
# Register the skills marketplace
/plugin marketplace add AdonaiVera/fiftyone-skills

# Install a skill
/plugin install fiftyone-find-duplicates@fiftyone-skills
```

### Step 4: Use It

```
Use the FiftyOne find duplicates skill to remove redundant images from my quickstart dataset
```

Claude will automatically load the skill instructions and execute the full workflow.

## How Skills Work

```
┌─────────────────────────────────────────────────────────────┐
│  FiftyOne MCP Server (16 tools)                             │
│  • Dataset management (list, load, summarize)               │
│  • Operator execution (80+ FiftyOne operators)              │
│  • Plugin management (install, enable, discover)            │
│  • Session control (launch/close App)                       │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │ orchestrates
                              │
┌─────────────────────────────────────────────────────────────┐
│  FiftyOne Skills (SKILL.md files)                           │
│  • Step-by-step workflow instructions                       │
│  • Key directives (ALWAYS/NEVER rules)                      │
│  • Concrete examples and troubleshooting                    │
└─────────────────────────────────────────────────────────────┘
```

## Skill Structure

Each skill is a markdown file with YAML frontmatter:

```
find-duplicates/
├── plugin.json
└── skills/
    └── fiftyone-find-duplicates/
        └── SKILL.md
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

# Examples
Concrete use cases
```

## Contributing

Want to create a skill?

1. Fork this repository
2. Copy an existing skill folder (e.g., `find-duplicates/`)
3. Update `SKILL.md` with your workflow
4. Update `.claude-plugin/marketplace.json`
5. Test with your AI assistant
6. Submit a Pull Request

See [find-duplicates SKILL.md](find-duplicates/skills/fiftyone-find-duplicates/SKILL.md) for a complete example.

## Alternative Installation Methods

### Codex

Codex uses `AGENTS.md` for skill discovery:

```bash
codex --ask-for-approval never "Summarize the current instructions."
```

### Gemini CLI

```bash
# Install locally
gemini extensions install . --consent

# Or via GitHub
gemini extensions install https://github.com/AdonaiVera/fiftyone-skills.git --consent
```

## Resources

- [FiftyOne Documentation](https://docs.voxel51.com)
- [FiftyOne MCP Server](https://github.com/AdonaiVera/fiftyone-mcp-server)
- [PyPI Package](https://pypi.org/project/fiftyone-mcp-server/)
- [MCP Registry](https://registry.modelcontextprotocol.io)
- [FiftyOne Plugins](https://github.com/voxel51/fiftyone-plugins)
- [Discord Community](https://discord.gg/fiftyone-community)

Copyright 2017-2025, Voxel51, Inc.

# FiftyOne Skills - Agent Instructions

This repository contains skills for computer vision workflows using FiftyOne and the FiftyOne MCP Server.

## Available Skills

### FiftyOne Find Duplicates (`find-duplicates/`)

**When to use:** User wants to find duplicate images, remove redundant samples, find similar images, or deduplicate a dataset.

**Instructions:** Load the skill file at `find-duplicates/skills/fiftyone-find-duplicates/SKILL.md`

**Key requirements:**
- FiftyOne MCP server must be running
- `@voxel51/brain` plugin must be installed
- FiftyOne App must be launched before using brain operators

**Workflow summary:**
1. Set context with dataset name
2. Launch FiftyOne App
3. Compute similarity embeddings
4. Find duplicates with threshold
5. Review and delete duplicates
6. Close app

### FiftyOne Dataset Inference (`dataset-inference/`)

**When to use:** User wants to load images/videos from a directory, import labeled datasets (COCO, YOLO, VOC), or run model inference on media files.

**Instructions:** Load the skill file at `dataset-inference/skills/fiftyone-dataset-inference/SKILL.md`

**Key requirements:**
- FiftyOne MCP server must be running
- `@voxel51/io` plugin for importing data
- `@voxel51/zoo` plugin for model inference
- `@voxel51/utils` plugin for dataset management

**Workflow summary:**
1. Explore directory to detect media and labels
2. Confirm findings with user
3. Create dataset and set context
4. Import samples (media only or with labels)
5. Validate import count
6. Launch App and run inference
7. View results and close app

### FiftyOne Embeddings Visualization (`embeddings-visualization/`)

**When to use:** User wants to visualize dataset in 2D, find clusters, identify outliers, color by class, explore embedding space, or understand data distribution.

**Instructions:** Load the skill file at `embeddings-visualization/skills/fiftyone-embeddings-visualization/SKILL.md`

**Key requirements:**
- FiftyOne MCP server must be running
- `@voxel51/brain` plugin must be installed
- FiftyOne App must be launched before using brain operators

**Workflow summary:**
1. Set context with dataset name
2. Launch FiftyOne App
3. Compute embeddings (CLIP, DINOv2, etc.)
4. Compute 2D visualization (UMAP/t-SNE)
5. View in App Embeddings panel
6. Color by field, find outliers, explore clusters
7. Close app

### FiftyOne Develop Plugin (`develop-plugin/`)

**When to use:** User wants to create, build, or develop a new FiftyOne plugin (operator or panel), extend FiftyOne with custom functionality, or integrate external APIs/services.

**Instructions:** Load the skill file at `develop-plugin/skills/fiftyone-develop-plugin/SKILL.md`

**Key requirements:**
- FiftyOne installed
- Python 3.8+ for Python plugins
- Node.js 16+ for JavaScript panels (optional)
- FiftyOne MCP server for testing

**Workflow summary:**
1. Gather requirements (purpose, type, inputs/outputs)
2. Search existing plugins for patterns
3. Design and plan the plugin structure
4. Generate code (fiftyone.yml, __init__.py, etc.)
5. Install plugin locally for testing
6. Iterate based on user feedback

**Reference files:**
- `PLUGIN-STRUCTURE.md` - Directory layout and fiftyone.yml
- `PYTHON-OPERATOR.md` - Python operator development
- `PYTHON-PANEL.md` - Python panel development
- `JAVASCRIPT-PANEL.md` - JavaScript/React panel development

### FiftyOne Code Style (`code-style/`)

**When to use:** User wants to write Python code following FiftyOne conventions, contribute to FiftyOne, or ensure code matches FiftyOne's style.

**Instructions:** Load the skill file at `code-style/skills/fiftyone-code-style/SKILL.md`

**Key patterns:**
- Module structure (docstring → imports → logger → public → private)
- Import organization (4 groups, FiftyOne aliases: fol, fou, etc.)
- Google-style docstrings with Args/Returns/Raises
- Lazy imports with `fou.lazy_import()`
- Guard patterns with `hasattr()`
- Error handling with `logger.warning()`

### FiftyOne PR Triage (`pr-triage/`)

**When to use:** User wants to triage GitHub issues, validate if bugs are fixed, categorize issue status, or generate standardized response messages.

**Instructions:** Load the skill file at `pr-triage/skills/fiftyone-pr-triage/SKILL.md`

**Triage categories:**
- Already Fixed - resolved in recent commits
- Won't Fix - by design or out of scope
- Not Reproducible - cannot reproduce with provided info
- No Longer Relevant - outdated version or stale
- Still Valid - confirmed bug or valid feature request

**Workflow summary:**
1. Read issue details and extract key info
2. Search codebase for related code
3. Check git history for fixes
4. Search closed issues/PRs for duplicates
5. Categorize and generate response

## Prerequisites

All skills require:

1. **FiftyOne MCP Server** installed and configured
   - Repository: https://github.com/AdonaiVera/fiftyone-mcp-server
   - Must be running and accessible

2. **FiftyOne** installed
   - Install: `pip install fiftyone`

3. **Required plugins** installed via FiftyOne
   - `@voxel51/brain` - For similarity and duplicates
   - `@voxel51/utils` - For dataset operations

## Integration

Skills work alongside the FiftyOne MCP Server:

- **MCP Server provides tools** - Low-level operations (list_datasets, execute_operator, etc.)
- **Skills provide workflows** - High-level guidance on how to use the tools

When a skill is active, use the FiftyOne MCP server tools to complete the workflow as described in the skill's SKILL.md file.

## General Workflow Pattern

Most FiftyOne skills follow this pattern:

1. Set context with `set_context` tool
2. Launch app with `launch_app` (for delegated operators)
3. Execute operators with `execute_operator`
4. Review results with `get_dataset_summary`
5. Close app with `close_app`

## Important Notes

- Delegated operators (brain, evaluation) require FiftyOne App to be running
- Always call `launch_app()` before using brain operators
- Wait 5-10 seconds after launching app before executing operators
- Close app with `close_app()` when workflow is complete

## Troubleshooting

**"No executor available" error:**
- Solution: Call `launch_app()` and wait for initialization

**"Operator not found" error:**
- Solution: Install and enable the required plugin

**"Context not set" error:**
- Solution: Call `set_context(dataset_name="...")` first

## Resources

- [FiftyOne Documentation](https://docs.voxel51.com)
- [FiftyOne MCP Server](https://github.com/AdonaiVera/fiftyone-mcp-server)
- [FiftyOne Plugins](https://github.com/voxel51/fiftyone-plugins)

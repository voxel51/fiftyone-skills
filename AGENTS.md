# FiftyOne Skills - Agent Instructions

This repository contains skills for computer vision workflows using FiftyOne and the FiftyOne MCP Server.

## Available Skills

<!-- BEGIN GENERATED SKILLS: do not edit, run `python scripts/generate_agents.py` -->

### FiftyOne App Playwright (`fiftyone-app-playwright/`)

Use when driving the FiftyOne App via the Playwright MCP — plugin/operator verification, demo or screencast recording, or any end-to-end UI automation against `fo.launch_app(...)`. Covers the critical "do not navigate after reload_dataset" crash, launcher patterns (remote=True, trigger-file IPC), MUI-specific input/dropdown gotchas, sidebar tag filtering, `data-cy` selectors, dialog scrolling, session refresh strategies, and cleanup. Trigger on mentions of "Playwright + FiftyOne", "automate FiftyOne App", "operator demo", "browser_navigate crash", "reload_dataset", or any FiftyOne session that silently dies after a UI action.

**Compatibility:** Requires the Playwright MCP server and a Python environment with `fiftyone` installed (drives a live `fo.launch_app(...)` session).

**Instructions:** Load the skill file at `skills/fiftyone-app-playwright/SKILL.md`

### FiftyOne Code Style (`fiftyone-code-style/`)

Writes Python code following FiftyOne's official conventions. Use when contributing to FiftyOne, developing plugins, or writing code that integrates with FiftyOne's codebase.

**Instructions:** Load the skill file at `skills/fiftyone-code-style/SKILL.md`

### FiftyOne Create Notebook (`fiftyone-create-notebook/`)

Creates Jupyter notebooks for FiftyOne workflows including getting-started guides, tutorials, recipes, and full ML pipelines. Use when creating notebooks, writing tutorials, building demos, or generating FiftyOne walkthroughs covering data loading, exploration, inference, evaluation, and export.

**Instructions:** Load the skill file at `skills/fiftyone-create-notebook/SKILL.md`

### FiftyOne Dataset Curation (`fiftyone-dataset-curation/`)

End-to-end dataset curation for FiftyOne: inspect schema and quality, audit annotations, analyze class distributions, explore embeddings, find duplicates, create curated subsets, and build train/val/test splits. Works with any computer vision dataset type.

**Instructions:** Load the skill file at `skills/fiftyone-dataset-curation/SKILL.md`

### FiftyOne Dataset Export (`fiftyone-dataset-export/`)

Exports FiftyOne datasets to standard formats (COCO, YOLO, VOC, CVAT, CSV, etc.) and Hugging Face Hub. Use when converting datasets, exporting for training, creating archives, sharing data in specific formats, or publishing datasets to Hugging Face.

**Instructions:** Load the skill file at `skills/fiftyone-dataset-export/SKILL.md`

### FiftyOne Dataset Import (`fiftyone-dataset-import/`)

Imports datasets into FiftyOne with automatic format detection. Supports all media types (images, videos, point clouds, MCAP multimodal recordings), label formats (COCO, YOLO, VOC, KITTI), multimodal grouped datasets, LeRobot v3 robot-learning episode datasets, and Hugging Face Hub datasets. Use when importing datasets from local files or Hugging Face, loading autonomous driving data, importing robotics/AV sensor logs (MCAP, ROS bag), importing LeRobot robot-learning episodes (teleop recordings, observation.state/action data), or creating grouped datasets.

**Instructions:** Load the skill file at `skills/fiftyone-dataset-import/SKILL.md`

### FiftyOne Dataset Inference (`fiftyone-dataset-inference/`)

Run ML model inference on FiftyOne datasets. Use when running models for detection, classification, segmentation, or embeddings. Discovers available models dynamically from the Zoo, plugin operators, or custom sources — never assumes a fixed model list.

**Instructions:** Load the skill file at `skills/fiftyone-dataset-inference/SKILL.md`

### FiftyOne Develop Plugin (`fiftyone-develop-plugin/`)

Develops custom FiftyOne plugins (operators and panels) from scratch. Use when creating plugins, extending FiftyOne with custom operators, building interactive panels, or integrating external APIs.

**Instructions:** Load the skill file at `skills/fiftyone-develop-plugin/SKILL.md`

### FiftyOne Embeddings Visualization (`fiftyone-embeddings-visualization/`)

Visualizes datasets in 2D using embeddings with UMAP or t-SNE dimensionality reduction. Use when exploring dataset structure, finding clusters, identifying outliers, or understanding data distribution.

**Instructions:** Load the skill file at `skills/fiftyone-embeddings-visualization/SKILL.md`

### FiftyOne Eval Plugin (`fiftyone-eval-plugin/`)

Evaluates FiftyOne plugins for quality, security, and agent-readiness. Use when reviewing a plugin before installation, auditing an existing plugin, validating a plugin you just built, or assessing community plugins for safety. Produces a structured report with scores and actionable recommendations.

**Instructions:** Load the skill file at `skills/fiftyone-eval-plugin/SKILL.md`

### FiftyOne Find Duplicates (`fiftyone-find-duplicates/`)

Finds duplicate or near-duplicate images in FiftyOne datasets using brain similarity computation. Use when deduplicating datasets, finding similar images, or removing redundant samples.

**Instructions:** Load the skill file at `skills/fiftyone-find-duplicates/SKILL.md`

### FiftyOne Generate Data Lens Connector (`fiftyone-generate-data-lens-connector/`)

Generate a Data Lens connector from an external database schema. Use when users want to connect an external data source (PostgreSQL, BigQuery, Databricks, MySQL, etc.) to FiftyOne Data Lens, or when they have a database schema and want to browse/import that data through the FiftyOne App.

**Instructions:** Load the skill file at `skills/fiftyone-generate-data-lens-connector/SKILL.md`

### FiftyOne Issue Triage (`fiftyone-issue-triage/`)

Triages FiftyOne GitHub issues by categorizing as fixed, won't fix, not reproducible, or still valid. Use when reviewing GitHub issues, triaging bugs, or closing stale issues in the voxel51/fiftyone repository.

**Instructions:** Load the skill file at `skills/fiftyone-issue-triage/SKILL.md`

### FiftyOne Model Evaluation (`fiftyone-model-evaluation/`)

Evaluate model predictions against ground truth using COCO, Open Images, or custom protocols. Use when computing mAP, precision, recall, confusion matrices, or analyzing TP/FP/FN examples for detection, classification, segmentation, or regression tasks.

**Instructions:** Load the skill file at `skills/fiftyone-model-evaluation/SKILL.md`

### FiftyOne SDK Guidance (`fiftyone-sdk-guidance/`)

Answers FiftyOne Python SDK questions with accurate, runnable code. Use when the user asks how to do something in the FiftyOne Python SDK, asks a docs question, no skill or operator covers their goal, or the agent is unsure of the correct FiftyOne method, argument, or field path while writing code — e.g. "how do I do X in Python", "show me the SDK for filtering", "there's no operator for this, can I do it in code", "what's the API for embeddings", "write me a Python script to do Y".

**Instructions:** Load the skill file at `skills/fiftyone-sdk-guidance/SKILL.md`

### FiftyOne Troubleshoot (`fiftyone-troubleshoot/`)

Diagnose and fix common FiftyOne issues automatically. Use when a dataset disappeared, the App won't open, changes aren't saving, MongoDB errors occur, video codecs fail, notebook connectivity breaks, operators are missing, or any recurring FiftyOne pain point needs solving.

**Instructions:** Load the skill file at `skills/fiftyone-troubleshoot/SKILL.md`

### FiftyOne VOODO Design (`fiftyone-voodo-design/`)

Build FiftyOne UIs using VOODO (@voxel51/voodo), the official React component library. Use when building plugin panels, creating interactive UIs, styling FiftyOne applications, or choosing components, text sizes, colors, and spacing. Looks up the installed version's components and token values with `npx @voxel51/voodo` before writing code.

**Instructions:** Load the skill file at `skills/fiftyone-voodo-design/SKILL.md`

### FiftyOne Zoo Remote Model (`fiftyone-zoo-remote-model/`)

Use when integrating a model into FiftyOne's remote model zoo — detection, classification, segmentation, embedding, keypoint, or vision-language (VLM) models loaded via `register_zoo_model_source` and `load_zoo_model`, then applied with `dataset.apply_model`. Also for debugging zoo registration, `manifest.json` issues, custom `fom.Model` / `TorchModelMixin` subclasses, DataLoader pickle errors, or worker `ModuleNotFoundError` from spawned DataLoader workers.

**Instructions:** Load the skill file at `skills/fiftyone-zoo-remote-model/SKILL.md`

<!-- END GENERATED SKILLS -->

## Prerequisites

All skills require:

1. **FiftyOne MCP Server** installed and configured
   - Repository: https://github.com/voxel51/fiftyone-mcp-server
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

## Session Tracking & Feedback

### WORK_LOG.md

Track session context to help debug issues and provide feedback:

**At START of session:**
- If `WORK_LOG.md` exists: Read it FIRST for project context
- If not: Ask if user wants to create one for tracking

**UPDATE when:**
- Problems solved
- Files created/modified
- Important decisions made
- Commands executed
- At END of substantial interactions

**Template:**
```markdown
# Project Work Log

## Session: YYYY-MM-DD HH:MM

### Context
- What we're working on

### Work Completed
- Changes, solutions, files modified

### Commands Executed
```bash
# Commands with results
```

### Decisions Made
- Choices and rationale

### Next Steps
- What remains, blockers

### References
- Relevant docs, links

---
```

**Guidelines:**
- Keep concise - summarize, don't dump conversations
- Reverse chronological (newest first)
- Serves as memory across sessions and context for feedback

### Submitting Feedback

When users want to report issues or provide feedback, **YOU (the agent) must automatically gather and summarize the actual session**:

1. **Summarize the conversation:**
   - What the user was trying to accomplish
   - What steps were taken
   - What went wrong or what feedback they have

2. **Report what was ACTUALLY USED (not all available):**
   - Your agent type (Claude Code, Cursor, Codex, etc.)
   - Skills that were invoked/used in THIS session
   - MCP tools that were called in THIS session
   - Read WORK_LOG.md if it exists

3. **Run environment commands:**
   ```bash
   python -c "import fiftyone; print(fiftyone.__version__)"
   pip show fiftyone-mcp-server | grep Version
   python --version
   ```

4. **Generate issue content** with gathered info:
   ```markdown
   ## Feedback

   **Type:** [Bug/Feature/Question]
   **Skill:** [skill that was used]

   ### Session Context
   - **Agent:** [your agent type]
   - **Skills Used:** [only skills invoked in this session]
   - **MCP Tools Used:** [only MCP tools called in this session]

   ### Conversation Summary
   [Summarize what the user was doing and what happened]

   ### Session Log
   [WORK_LOG.md excerpts if available]

   ### Environment
   - FiftyOne: [version]
   - MCP Server: [version]
   - Python: [version]
   ```

5. **Offer to submit directly** or provide content to paste:
   ```bash
   # Submit directly via gh CLI
   gh issue create --repo voxel51/fiftyone-skills \
     --title "[Feedback]: Brief description" \
     --body "$(cat <<'EOF'
   [generated content here]
   EOF
   )"
   ```
   Or provide content to paste at: https://github.com/voxel51/fiftyone-skills/issues/new

## Resources

- [FiftyOne Documentation](https://docs.voxel51.com)
- [FiftyOne LLM Docs](https://docs.voxel51.com/llms.txt) - Fetch this for comprehensive FiftyOne API reference
- [FiftyOne MCP Server](https://github.com/voxel51/fiftyone-mcp-server)
- [FiftyOne Plugins](https://github.com/voxel51/fiftyone-plugins)
- [VOODO Design System](https://voodo.dev.fiftyone.ai/) - Storybook; for React component docs run `npx @voxel51/voodo docs <Name>`

## External Documentation

When you need detailed FiftyOne API information beyond what's in the skills, fetch:
- `https://docs.voxel51.com/llms.txt` - Complete FiftyOne documentation for LLMs
- VOODO React component docs: run `npx @voxel51/voodo docs <Name>` in a project that installs `@voxel51/voodo`

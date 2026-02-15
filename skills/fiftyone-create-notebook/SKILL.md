---
name: fiftyone-create-notebook
description: Creates Jupyter notebooks for FiftyOne workflows including getting-started guides, tutorials, recipes, and full ML pipelines. Use when creating notebooks, writing tutorials, building demos, or generating FiftyOne walkthroughs covering data loading, exploration, inference, evaluation, and export.
---

# Create FiftyOne Notebooks

## Contents
- [Key Directives](#key-directives)
- [Complete Workflow](#complete-workflow)
- [Notebook Structure Reference](#notebook-structure-reference)
- [Common Use Cases](#common-use-cases)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)
- [Resources](#resources)

## Key Directives

**ALWAYS follow these rules:**

### 1. Determine notebook type first

Classify the user's request before anything else:

| User Request Pattern | Type | Template |
|---|---|---|
| "getting started", "beginner", "intro", "first notebook" | Getting Started | [GETTING-STARTED-TEMPLATES.md](GETTING-STARTED-TEMPLATES.md) |
| "tutorial", "how to use X", "deep dive", "demonstrate X" | Tutorial | [TUTORIAL-TEMPLATES.md](TUTORIAL-TEMPLATES.md) |
| "recipe", "quick", "snippet", "how do I X" | Recipe | [RECIPE-TEMPLATES.md](RECIPE-TEMPLATES.md) |
| "full pipeline", "end to end", "ML pipeline", "complete workflow" | Full Pipeline | [GETTING-STARTED-TEMPLATES.md](GETTING-STARTED-TEMPLATES.md) with all stages |

If ambiguous, ask the user.

### 2. Create the notebook file before adding cells

Use the Write tool to create a valid empty `.ipynb` file first:

```json
{
  "nbformat": 4,
  "nbformat_minor": 2,
  "metadata": {
    "kernelspec": {
      "display_name": "Python 3",
      "language": "python",
      "name": "python3"
    },
    "language_info": {
      "name": "python",
      "version": "3.10.0"
    }
  },
  "cells": []
}
```

Then use `NotebookEdit` with `edit_mode: "insert"` to add cells.

### 3. Follow FiftyOne code conventions

All generated code must use standard FiftyOne import aliases:

```python
import fiftyone as fo
import fiftyone.zoo as foz
import fiftyone.brain as fob
import fiftyone.types as fot
from fiftyone import ViewField as F
```

See the "Code Pattern Sources" table below for full conventions.

### 4. Build notebooks cell-by-cell

Use `NotebookEdit` with `edit_mode: "insert"` for every cell. Build top-to-bottom using `cell_id` chaining: insert the first cell without `cell_id` (inserts at beginning), then read the notebook to get its `cell_id`, and insert each subsequent cell with `cell_id` set to the previous cell's ID. This ensures correct ordering.

**Critical:** Without `cell_id`, every insert goes to the **beginning** of the notebook, resulting in reversed cell order.

**Never** write the entire `.ipynb` JSON at once. Incremental cell insertion allows verification and correction.

### 5. Always include App visualization

Every notebook must include at least one cell with:

```python
session = fo.launch_app(dataset)
```

FiftyOne's core value is visual exploration. Notebooks without App visualization miss the point.

### 6. Use zoo datasets when user has no data

For getting-started and tutorial notebooks, default to `foz.load_zoo_dataset()` so users can run the notebook without bringing their own data. For recipes and custom pipelines, support both zoo and user data.

### 7. Precede every code cell with a markdown cell

Never place two code cells in a row without a markdown cell in between. The markdown cell explains **what** the code does and **why**. This is critical for tutorials and getting-started guides. Recipes are exempt — consecutive code cells are permitted for brevity (imports + load data, core solution + verify).

### 8. Present outline before generating

Before creating any cells, draft a notebook outline showing:
- Section headings
- Cell types (markdown/code)
- Brief description of each cell

Get user approval before generating.

### 9. Fetch current API documentation

When generating code, fetch `https://docs.voxel51.com/llms.txt` for the latest FiftyOne API patterns. This ensures generated code uses current APIs and avoids deprecated patterns.

### 10. Verify after generation

After all cells are inserted, read the notebook back with the Read tool to verify:
- Cells are in correct order
- Markdown/code alternation is maintained
- Import aliases are correct
- Narrative flow is logical

## Complete Workflow

### Phase 1: Requirements

Gather information before designing the notebook:

1. **Classify notebook type** — Use the decision matrix from Directive 1. Ask the user if ambiguous.
2. **Determine domain and task** — Ask or infer what ML task the notebook covers. Common domains include:
   - Object Detection
   - Image Classification
   - Instance/Semantic Segmentation
   - Embeddings & Similarity
   - Data Curation (duplicates, outliers, annotation mistakes)
   - Video analysis, 3D point clouds, or any other FiftyOne-supported workflow
3. **Determine data source:**
   - **Zoo dataset** (recommended for tutorials): `foz.load_zoo_dataset("coco-2017", ...)`
   - **User's local data**: `fo.Dataset.from_dir(...)`
   - **Hugging Face Hub**: `foz.load_zoo_dataset("https://huggingface.co/datasets/...", ...)`
   - **Quickstart**: `foz.load_zoo_dataset("quickstart")`
4. **Determine pipeline stages:**

| Stage | Description | Always Include? |
|---|---|---|
| Data Loading | Load/create dataset | Yes |
| Exploration | App, stats, filtering | Yes |
| Brain Methods | Embeddings, uniqueness, duplicates | If relevant |
| Inference | Model predictions | If relevant |
| Evaluation | Metrics, TP/FP/FN analysis | If predictions + ground truth |
| Export | Save to format | Optional |

5. **Confirm with user** — Present a summary:
   - Notebook type: [Getting Started / Tutorial / Recipe / Full Pipeline]
   - Domain: [Detection / Classification / ...]
   - Data source: [Zoo dataset name / User path / HF URL]
   - Pipeline stages: [Load, Explore, Infer, Evaluate, Export]
   - Estimated cells: [N]

### Phase 2: Design

1. **Read the appropriate template doc** as a structural guide (adapt to the user's domain — do not copy specific datasets, models, or field names from the examples):
   - [GETTING-STARTED-TEMPLATES.md](GETTING-STARTED-TEMPLATES.md) for getting-started and full pipeline
   - [TUTORIAL-TEMPLATES.md](TUTORIAL-TEMPLATES.md) for tutorials
   - [RECIPE-TEMPLATES.md](RECIPE-TEMPLATES.md) for recipes
2. **Fetch API documentation** — Fetch `https://docs.voxel51.com/llms.txt` using the WebFetch tool for current FiftyOne API patterns. This is the authoritative source for SDK usage.
3. **Draft notebook outline** — Create a numbered list of cells with cell number, type (markdown/code), and content summary:
```
0. [markdown] Title + description
1. [markdown] What You Will Learn
2. [code] pip install
3. [markdown] ## Setup
4. [code] Imports
5. [markdown] ## Load Dataset
6. [code] Load from zoo + print dataset info
...
```
4. **Present outline for approval** — Show the outline to the user. Wait for approval before generating.

### Phase 3: Generation

1. **Create empty notebook file:**
```python
# Use Write tool
Write(
    file_path="/path/to/notebook.ipynb",
    content='{"nbformat": 4, "nbformat_minor": 2, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3.10.0"}}, "cells": []}'
)
```
Ask the user for the notebook file path, or suggest a default based on the title.

2. **Add cells with NotebookEdit using `cell_id` chaining:**

Insert the first cell without `cell_id` (goes to beginning), then read the notebook to get the assigned `cell_id`. Each subsequent cell uses `cell_id` of the previous cell:
```
# First cell — no cell_id, inserts at beginning
NotebookEdit(
    notebook_path="/path/to/notebook.ipynb",
    new_source="# Title\n\nDescription paragraph.",
    cell_type="markdown",
    edit_mode="insert"
)

# Read notebook to get the first cell's ID (e.g., "cell-0")
Read(file_path="/path/to/notebook.ipynb")

# Second cell — chain after cell-0
NotebookEdit(
    notebook_path="/path/to/notebook.ipynb",
    cell_id="cell-0",
    new_source="!pip install -q fiftyone",
    cell_type="code",
    edit_mode="insert"
)

# Third cell — chain after cell-1
NotebookEdit(
    notebook_path="/path/to/notebook.ipynb",
    cell_id="cell-1",
    new_source="import fiftyone as fo",
    cell_type="code",
    edit_mode="insert"
)
```
Continue chaining: each new cell's `cell_id` = previous cell's ID (cell-0, cell-1, cell-2, ...).

**Cell content guidelines:**
- Keep code cells under 15 lines
- One concept per code cell
- Include inline comments for non-obvious operations
- Use `print()` liberally so users see output
- Include `# Expected output:` comments where helpful

3. **Review during generation** — After every 5-10 cells, briefly verify the notebook is building correctly. Read it back if needed.

### Phase 4: Validation

1. **Read notebook back** — Use the Read tool to read the entire `.ipynb` file. Verify:
   - Total cell count matches outline
   - Cell order is correct
   - No missing sections
2. **Verify code quality** — Check all code cells for:
   - Correct FiftyOne import aliases (`fo`, `foz`, `fob`, `fot`, `F`)
   - No deprecated APIs
   - Consistent variable names throughout
   - `dataset` variable used consistently
   - Field names match between inference, evaluation, and filtering cells
3. **Verify narrative flow** — Check markdown cells for:
   - Logical progression from section to section
   - No jargon without explanation (for getting-started)
   - Each markdown cell explains the **why**, not just the **what**
4. **Execute the notebook** — Create an isolated virtual environment and run end-to-end with `papermill` to avoid modifying the user's system Python:
   ```bash
   python -m venv .notebook-test-env
   .notebook-test-env/bin/pip install -q papermill ipykernel anywidget
   .notebook-test-env/bin/python -m ipykernel install --user --name python3 --display-name "Python 3"
   .notebook-test-env/bin/papermill notebook.ipynb notebook_output.ipynb
   ```
   Fix any runtime errors, then re-run until all cells pass. Clean up after: `rm -rf .notebook-test-env`. Common issues:
   - `session.view` requires a `DatasetView`, not a `Dataset` — use `dataset.view()`
   - Missing packages — add them to the notebook's install cell
   - Plotly widgets need `anywidget` in headless environments
5. **Present summary** — Tell the user:
   - Notebook path
   - Total cells (N markdown + N code)
   - Sections covered
   - Execution status (all cells passed / errors fixed)
   - How to run it (e.g., `jupyter notebook path/to/notebook.ipynb`)

## Notebook Structure Reference

See [NOTEBOOK-STRUCTURE.md](NOTEBOOK-STRUCTURE.md) for detailed cell structure patterns for each pipeline stage, including cell shapes and markdown patterns.

### Code Pattern Sources

For actual code patterns, fetch `https://docs.voxel51.com/llms.txt` as the authoritative source. Related skills provide additional context for specific pipeline stages:

| Pipeline Stage | Related Skill |
|---|---|
| Imports & conventions | [fiftyone-code-style](../fiftyone-code-style/SKILL.md) |
| Data loading | [fiftyone-dataset-import](../fiftyone-dataset-import/SKILL.md) |
| Inference | [fiftyone-dataset-inference](../fiftyone-dataset-inference/SKILL.md) |
| Evaluation | [fiftyone-model-evaluation](../fiftyone-model-evaluation/SKILL.md) |
| Export | [fiftyone-dataset-export](../fiftyone-dataset-export/SKILL.md) |
| Embeddings & visualization | [fiftyone-embeddings-visualization](../fiftyone-embeddings-visualization/SKILL.md) |
| Duplicates | [fiftyone-find-duplicates](../fiftyone-find-duplicates/SKILL.md) |

## Common Use Cases

### Use Case 1: Getting Started with Object Detection

**User says:** "Create a getting-started notebook for object detection"

**Notebook outline (21 cells):**

| Cell | Type | Content |
|---|---|---|
| 0 | markdown | `# Getting Started with Object Detection in FiftyOne` |
| 1 | markdown | What You Will Learn (bullet list) |
| 2 | code | `!pip install fiftyone ultralytics` |
| 3 | markdown | ## Setup |
| 4 | code | Imports (`fo`, `foz`, `F`) |
| 5 | markdown | ## Load Dataset |
| 6 | code | `dataset = foz.load_zoo_dataset(...)` + `print(dataset)` + `print(dataset.first())` |
| 7 | markdown | ## Explore in the FiftyOne App |
| 8 | code | `session = fo.launch_app(dataset)` |
| 9 | markdown | ## Understand the Data |
| 10 | code | `dataset.count_values("ground_truth.detections.label")` |
| 11 | markdown | ## Run Model Inference |
| 12 | code | `model = foz.load_zoo_model(...)` + `dataset.apply_model(...)` + `session.view = dataset.view()` |
| 13 | markdown | ## Evaluate Predictions |
| 14 | code | `dataset.evaluate_detections(...)` + `results.print_report()` |
| 15 | markdown | ## Analyze Errors |
| 16 | code | Evaluation patches: `dataset.to_evaluation_patches("eval")`, filter to FP |
| 17 | markdown | ## Export for Training |
| 18 | code | `dataset.export(...)` to YOLOv5 format |
| 19 | markdown | ## Conclusion + Next Steps |
| 20 | code | Cleanup: `fo.delete_dataset(...)` |

### Use Case 2: Tutorial - Finding Annotation Mistakes

**User says:** "Write a tutorial on finding annotation mistakes with FiftyOne"

**Notebook outline (29 cells):**

| Phase | Cells | Content |
|---|---|---|
| Introduction | 0-2 | Title, problem statement (why annotation quality matters), learning goals |
| Setup | 3-4 | pip install, imports |
| Data | 5-8 | Load detection dataset, inspect schema, explore class distribution, launch App |
| Concept | 9-10 | Explain mistakenness: what it is, how it works, why embeddings help |
| Compute | 11-14 | Compute embeddings, compute mistakenness, view mistakenness distribution |
| Explore | 15-18 | Sort by mistakenness, view worst samples in App, tag suspicious annotations |
| Hardness | 19-22 | Compute hardness, compare with mistakenness, find ambiguous samples |
| Action | 23-25 | Filter to flagged samples, export for re-annotation |
| Conclusion | 26-28 | Summary, key takeaways, next steps, cleanup |

### Use Case 3: Recipe - Export to COCO Format

**User says:** "Quick recipe to export my dataset to COCO format"

**Notebook outline (7 cells):**

| Cell | Type | Content |
|---|---|---|
| 0 | markdown | `# Export a FiftyOne Dataset to COCO Format` + one sentence description |
| 1 | code | `import fiftyone as fo` + `import fiftyone.types as fot` |
| 2 | code | `dataset = fo.load_dataset("my-dataset")` |
| 3 | markdown | Brief explanation of COCO format |
| 4 | code | `dataset.export(export_dir="/tmp/coco-export", dataset_type=fot.COCODetectionDataset, label_field="ground_truth")` |
| 5 | code | Verify: `!ls /tmp/coco-export/` |
| 6 | markdown | Variations: export with filters, export labels only, export to YOLOv5 |

### Use Case 4: Full ML Pipeline

**User says:** "Create a complete ML pipeline notebook"

**Notebook outline (31 cells):**

| Phase | Cells | Content |
|---|---|---|
| Title | 0-1 | Title + learning goals |
| Setup | 2-3 | pip install + imports |
| Load | 4-6 | Load dataset, inspect, print schema |
| Explore | 7-10 | Launch App, class distribution, sample statistics, filtering |
| Deduplicate | 11-13 | Compute embeddings, find near-duplicates, remove duplicates |
| Infer | 14-16 | Load model, apply to dataset, view predictions in App |
| Evaluate | 17-21 | Run evaluation, print report, confusion matrix, PR curves, patches |
| Visualize | 22-24 | Compute UMAP visualization, explore embedding space, find clusters |
| Export | 25-27 | Export curated dataset, export to training format |
| Conclusion | 28-30 | Summary, next steps, cleanup |

## Troubleshooting

**Error: "Cells appear in wrong order"**
- Cause: Inserting cells without `cell_id` — each insert without `cell_id` goes to the **beginning** of the notebook, resulting in reversed order
- Solution: Use `cell_id` chaining (see Directive 4). Insert first cell without `cell_id`, read notebook to get its ID, then chain each subsequent cell after the previous one. Use `edit_mode: "replace"` to fix individual cells.

**Error: "Empty notebook after generation"**
- Cause: Write tool did not create valid JSON structure
- Solution: Verify the minimal `.ipynb` JSON includes `"cells": []` and `"nbformat": 4`

**Error: "Import errors in generated code"**
- Cause: Using deprecated or incorrect FiftyOne APIs
- Solution: Fetch `https://docs.voxel51.com/llms.txt` before generating code. Use standard aliases: `fo`, `foz`, `fob`, `fot`, `F`. Check that pip install cell includes all required packages.

**Error: "Generated code uses deprecated APIs"**
- Cause: Stale API patterns
- Solution: Fetch `https://docs.voxel51.com/llms.txt` for current API. Common deprecation: `dataset.count("field")` → `dataset.count_values("field")`

**Error: "Notebook doesn't render in Jupyter"**
- Cause: Invalid `.ipynb` JSON structure
- Solution: Verify `"nbformat": 4` is set and `"cells"` is an array, not null

## Best Practices

1. **Keep code cells short** - Under 15 lines, one concept per cell
2. **Use markdown liberally** - Every code cell should have a markdown cell explaining it
3. **Show output** - Use `print()` and display so users see intermediate results
4. **Include App visualization** - At least one `fo.launch_app()` call per notebook
5. **Use zoo datasets for demos** - Makes notebooks immediately runnable
6. **Include cleanup** - Add a cleanup cell at the end to delete temporary datasets
7. **Link to docs** - Include links to relevant FiftyOne documentation
8. **Progressive complexity** - Start simple, build to complex
9. **Explain the "why"** - Don't just show code; explain why each step matters
10. **Test your outline first** - Get user approval on the structure before generating 30+ cells

## Resources

- [FiftyOne Documentation](https://docs.voxel51.com)
- [FiftyOne LLM Docs](https://docs.voxel51.com/llms.txt) - Fetch for comprehensive API reference
- [FiftyOne Tutorials](https://docs.voxel51.com/tutorials/index.html)
- [FiftyOne Recipes](https://docs.voxel51.com/recipes/index.html)
- [FiftyOne Model Zoo](https://docs.voxel51.com/model_zoo/index.html)
- [FiftyOne User Guide](https://docs.voxel51.com/user_guide/index.html)

---
name: fiftyone-dataset-curation
description: End-to-end dataset curation for FiftyOne: inspect schema and quality, audit annotations, analyze class distributions, explore embeddings, find duplicates, create curated subsets, and build train/val/test splits. Works with any computer vision dataset type.
---

# FiftyOne Dataset Curation

End-to-end curation pipeline for any FiftyOne dataset: images, video, point clouds, grouped multimodal. Run all phases sequentially or jump directly to any single phase.

## Key Directives

**ALWAYS follow these rules — no exceptions:**

### 1. Check for a loaded dataset first
```
list_datasets()
```
If none exists, offer to delegate to `fiftyone-dataset-import` skill.

### 2. Set context before any operation
```
set_context(dataset_name="<name>")
```

### 3. Launch App before any brain operator
```
launch_app()
```
Wait 5–10 seconds for initialization before executing delegated operators.

### 4. Discover schema before referencing any field
```
dataset_summary()
get_field_schema(flat=True)
```
Never hardcode field names. Adapt all field references from schema discovery results.

### 5. Discover operators dynamically
```
list_operators(builtin_only=False)
get_operator_schema(operator_uri="<uri>")
```
Always call `list_operators()` before any `execute_operator()`. Confirm the operator exists.

### 6. Confirm before mutating
Before tagging, adding fields, or deleting — present findings to the user and ask for confirmation.

### 7. Keep App open for interactive review
Do NOT call `close_app()` automatically. Leave the App running so the user can explore results.

### 8. Check delegated service before brain operations
Before running any brain operator with `delegate=True`, verify the delegated service is running:
```bash
fiftyone delegated list
```
If no services are running:
```bash
fiftyone delegated launch &
```
Wait ~5 seconds for initialization. Without this service, delegated operators will queue but never execute.

### 9. Always discover plugin names dynamically
Never assume a plugin's exact name or operator URI from documentation. Always verify:
```
list_plugins()
```
Use the exact plugin name from the output. Then:
```
list_operators(builtin_only=False)
```
Use the exact operator URI from the output. Documentation names may differ from installed names.

### 10. Generate interactive insights after each phase
After computing any metric (uniqueness, quality, similarity, etc.):
1. Calculate counts of flagged/notable samples
2. Create named saved views for the findings
3. Load the view in the App automatically
4. Present a narrative insight to the user
5. Offer to continue to the next phase

See **Insight Generation Pattern** at the bottom of this file.

---

## Phase -1 — Curation Plan

**Before doing anything else**, present a complete curation plan to the user. This sets expectations and allows them to choose which phases to run.

```
list_datasets()
dataset_summary()
get_field_schema(flat=True)
```

Present the plan:

```
## Curation Plan for <dataset_name>

Dataset: <name> | <N> samples | <media_type>
Label fields: <list from schema>
Existing brain runs: <list or "none">

### Phases I will run:
  Phase 1 — Dataset Inspection        (schema, tags, class distribution)
  Phase 2 — Data Quality Audit        (metadata, resolution, file size, image quality via jacobmarks/image_issues plugin)
  Phase 3 — Near-Duplicate Detection  (via fiftyone-find-duplicates skill)
  Phase 4 — Class Distribution        (imbalance, coverage gaps)
  Phase 5 — Embedding Exploration     (CLIP UMAP, gap detection)
  Phase 6 — Annotation Audit          (mistakenness — requires predictions field)
  Phase 7 — Curated Subset & Splits   (clean view, train/val/test)
  Phase 8 — Data Q&A                  (on-demand questions)

### Phases I will SKIP (and why):
  Phase 6 — No predictions field found. Run fiftyone-dataset-inference first.

### What you'll get:
  - Named saved views for each key finding (loadable in App)
  - Interactive insights at each step
  - A clean_<dataset_name> view with quality filters applied

Ready to start? (yes / skip to phase X / select specific phases)
```

Wait for user confirmation before proceeding. If they want to skip phases or run only specific ones, adapt accordingly.

---

## Phase 0 — Dataset Loading (Optional)

Run this phase only if no dataset is loaded yet.

```
list_datasets()
```

- If a dataset exists → `set_context(dataset_name="<name>")` and proceed to Phase 1.
- If no dataset exists → delegate to `fiftyone-dataset-import` skill.

After loading:
```
dataset_summary()
```

Confirm with user:
- Media type (image, video, point-cloud, group)
- Sample count
- Whether `persistent=True` is set

---

## Phase 1 — Dataset Inspection

**MCP tools:** `dataset_summary`, `get_field_schema`, `count_values`, `distinct`

### Steps

```
dataset_summary()
get_field_schema(flat=True)
count_values("tags")
```

From the schema, identify label fields (Detections, Classifications, Keypoints, Segmentation, Polylines, etc.) and run:
```
distinct("<label_field>.label")
```
Adapt the field path from the schema — never assume a field name.

### Report to user

Present a summary with:
- Media type and sample count
- All field names and their types
- Existing tags and counts
- Unique class names per label field
- Any existing brain runs (embeddings, similarity indexes, mistakenness scores)
- Missing or empty fields (flag these)
- **Label type awareness**: Note whether label fields are Classifications vs. Detections — this affects which export formats are valid later

### Export format note

After identifying label types, inform the user:
```
Label type: Classification → supports Image Classification Directory Tree export
Label type: Detection → supports COCO, YOLO, VOC export
For COCO export with Classification labels → must run inference first (fiftyone-dataset-inference) to generate Detection labels
```

### Grouped dataset detection

If `dataset_summary()` reports `media_type == "group"`:
1. List available group slices from the schema
2. Recommend operating on individual sensor slices for all curation phases:
   ```python
   # Python SDK equivalent (use for user guidance)
   rgb_view = dataset.select_group_slices(["rgb_center"])
   dataset.save_view("rgb_view", rgb_view)
   ```
3. Apply all subsequent brain operations to the slice view, not the full grouped dataset
4. Use sensor-prefixed brain keys (e.g., `rgb_clip_umap`, `ir_clip_umap`)

### Existing brain runs

If brain runs are reported in `dataset_summary()`:
- List them and their types (similarity, visualization, mistakenness, uniqueness, etc.)
- Offer to reuse existing runs instead of recomputing
- Ask user which phases to run and whether to skip phases with existing results

---

## Phase 2 — Data Quality Audit

See `QUALITY-CHECKS.md` for the full deep-dive workflow.

**MCP tools:** `execute_operator`, `bounds`, `histogram_values`, `mean`, `std`, `count_values`, `set_view`, `list_plugins`, `download_plugin`, `enable_plugin`

### Minimum steps

**Step 1: Compute metadata**
```
list_operators(builtin_only=False)
get_operator_schema(operator_uri="@voxel51/utils/compute_metadata")
execute_operator(operator_uri="@voxel51/utils/compute_metadata", params={})
```

**Step 2: Check for corruption (null metadata)**
```
set_view(filters={"metadata": null})
```
If samples appear → report count; offer to tag them as `"corrupted"` after confirmation.

**Step 3: Resolution analysis**
```
bounds("metadata.width")
bounds("metadata.height")
histogram_values("metadata.width", bins=20)
histogram_values("metadata.height", bins=20)
```

**Step 4: File size analysis**
```
bounds("metadata.size_bytes")
mean("metadata.size_bytes")
std("metadata.size_bytes")
```

**Step 5: Aspect ratio**
Report wide/tall outliers using ViewField pattern (see QUALITY-CHECKS.md).

**Step 6: Image quality via jacobmarks plugin (REQUIRED for image datasets)**

This is the primary method for detecting blur, brightness issues, contrast, saturation, and aspect ratio anomalies. Do NOT use custom cv2 code. Follow the discovery workflow:

```
list_plugins()
```

Find the entry matching "image_issues" or "image-quality". Note the exact plugin name from the output — **do not assume it matches the documentation name**.

If not installed:
```
download_plugin(plugin_name="jacobmarks/image-quality-issues")
```
Then run `list_plugins()` again to confirm the installed name.

Enable if disabled:
```
enable_plugin(plugin_name="<exact_name_from_list_plugins>")
```

Discover operator URIs:
```
list_operators(builtin_only=False)
```

Find operators matching `find_issues`, `compute_blurriness`, `compute_brightness`, etc. Use exact URIs.

Run each issue check (delegated, one at a time). Use the exact operator URI from `list_operators()`:
```
execute_operator(
    operator_uri="<uri_from_list_operators>",   # e.g. @jacobmarks/image_issues/find_issues
    params={"issue_mode": "SINGLE", "issue": "blurry"},
    delegate=True
)
```

Wait for completion via `list_delegated_operations()` before running the next issue check. Repeat for: `low_contrast`, `low_saturation`, `weird_aspect_ratio`, `dark`, `bright` (see note on `bright` in QUALITY-CHECKS.md).

After all checks complete:
```
get_field_schema(flat=True)
```
Identify the boolean flag fields added (e.g., `blurry`, `low_contrast`, `low_saturation`, `weird_aspect_ratio`).

Generate interactive insights — see **Insight Generation Pattern** below.

---

## Phase 3 — Near-Duplicate Detection

**Delegate to `fiftyone-find-duplicates` skill.**

Tell the user:
> "For near-duplicate detection, I'll use the `fiftyone-find-duplicates` skill."

Recommended settings to suggest:
- Model: `mobilenet-v2-imagenet-torch` (fast) or `clip-vit-base32-torch` (semantic)
- Brain key: `img_sim`
- Default threshold: 0.3

After duplicates are identified and optionally removed, return here for Phase 4.

---

## Phase 4 — Class Distribution & Imbalance Analysis

**MCP tools:** `count_values`, `histogram_values`, `distinct`, `bounds`, `mean`, `std`

For each label field discovered in Phase 1:

### Classification datasets
```
count_values("<label_field>.label")
```

### Detection datasets
```
count_values("<detections_field>.detections.label")
histogram_values("<detections_field>.detections.confidence", bins=20)
bounds("<detections_field>.detections.bounding_box")
mean("<detections_field>.detections.confidence")
```

### Analysis to surface

- **Class imbalance**: Classes with < 5% of total samples are underrepresented — flag them
- **Confidence spread**: Bimodal distribution suggests uncertain predictions
- **BBox size range**: Very small bboxes (< 1% of image area) may be low-quality annotations
- **Metadata distributions**: If metadata fields exist (time of day, weather, sensor type, etc.), run `count_values` on them to surface coverage gaps:
  ```
  count_values("<metadata_field>")
  ```
  Adapt field paths from schema — do not assume any specific metadata fields exist.

### Coverage gaps

Report under-represented attribute combinations. Example guidance:
- Few night-scene samples → recommend semantic search augmentation (Phase 5)
- Rare class < 20 samples → flag for annotation priority

---

## Phase 5 — Embedding Exploration & Gap Detection

**Delegate to `fiftyone-embeddings-visualization` skill.**

Tell the user:
> "For embedding visualization and gap detection, I'll use the `fiftyone-embeddings-visualization` skill."

### Critical parameter: num_dims

When calling `compute_visualization`, always include `num_dims`:
```
execute_operator(
    operator_uri="@voxel51/brain/compute_visualization",
    params={
        "brain_key": "<key>",
        "model": "clip-vit-base32-torch",
        "method": "umap",
        "num_dims": 2        # REQUIRED — operator fails without this
    },
    delegate=True
)
```

### UMAP dependency

`umap-learn` must be installed in the same Python environment as FiftyOne. If it fails:
```bash
# Find which python FiftyOne uses
python3 -c "import fiftyone; print(fiftyone.__file__)"

# Install to the correct environment
/path/to/correct/python -m pip install umap-learn
```

### Recommended models

- **CLIP** (`clip-vit-base32-torch`): Semantic similarity, supports text search → best for gap detection
- **DINOv2** (`dinov2-vits14-torch`): Visual similarity → best for cluster exploration

### Patch-level embeddings (detection datasets)

For detection datasets, suggest patch-level embeddings after schema confirms a detections field:
```
get_operator_schema(operator_uri="@voxel51/brain/compute_visualization")
execute_operator(
    operator_uri="@voxel51/brain/compute_visualization",
    params={
        "patches_field": "<detections_field>",   # from schema discovery
        "model": "clip-vit-base32-torch",
        "method": "umap",
        "num_dims": 2,
        "brain_key": "<detections_field>_clip_umap"
    },
    delegate=True
)
```

### Uniqueness computation

After UMAP/similarity completes, compute uniqueness to find redundant samples:
```
execute_operator(
    operator_uri="@voxel51/brain/compute_uniqueness",
    params={},
    delegate=True
)
```

After completion, generate interactive insights:
```
bounds("uniqueness")
histogram_values("uniqueness", bins=20)
```

Build named views:
```python
# Python SDK guidance — present these commands to user
# Most redundant: bottom uniqueness scores
dataset.save_view("redundant_samples", dataset.sort_by("uniqueness").limit(N))
# Most diverse: top uniqueness scores
dataset.save_view("most_unique", dataset.sort_by("uniqueness", reverse=True).limit(M))
```

Then load the insight view:
```
execute_operator("@voxel51/operators/load_saved_view", params={"name": "most_unique"})
```

### Semantic text search for subset discovery

After CLIP similarity index exists:
```
execute_operator(
    operator_uri="@voxel51/brain/sort_by_similarity",
    params={"query": "foggy day", "k": 50, "brain_key": "<sim_key>"}
)
tag_samples(["foggy"])
```
Use text queries that match domain gaps found in Phase 4.

---

## Phase 6 — Annotation Audit

See `ANNOTATION-AUDIT.md` for the full deep-dive workflow.

**MCP tools:** `execute_operator`, `get_field_schema`, `set_view`, `tag_samples`

### Prerequisite check

Check if a predictions field exists:
```
get_field_schema(flat=True)
```

If no predictions field:
> "Annotation audit (mistakenness) requires a predictions field. Delegate to `fiftyone-dataset-inference` skill first, then return here."

> Note: If the dataset has Classification labels and you want COCO-compatible predictions, use `yolov8n-coco-torch` from the Zoo — it generates actual Detection bounding boxes.

### Steps

**Step 1: Compute mistakenness**
```
list_operators(builtin_only=False)
get_operator_schema(operator_uri="@voxel51/brain/compute_mistakenness")
execute_operator(
    operator_uri="@voxel51/brain/compute_mistakenness",
    params={
        "pred_field": "<predictions_field>",    # from schema
        "label_field": "<ground_truth_field>",  # from schema
        "mistakenness_field": "mistakenness"
    }
)
```

**Step 2: Review high-mistakenness samples**
```
set_view(sort_by="mistakenness", reverse=True, limit=50)
```
Direct user to the FiftyOne App (use get_session_info() to get the URL) for visual review.

**Step 3: Tag suspicious samples** (after user confirmation)
```
tag_samples(["annotation_review"])
```

**Step 4: Check possible missing annotations**
```
set_view(filters={"possible_missing": {"$gt": 0}})
```

Full annotation audit workflow in `ANNOTATION-AUDIT.md`.

---

## Phase 7 — Curated Subset Creation & Splits

See `SUBSET-CREATION.md` for the full deep-dive workflow.

**MCP tools:** `execute_operator`, `tag_samples`, `untag_samples`, `set_view`

### Building the clean view

After quality checks and duplicate detection, construct a clean view by combining all quality filters. Use `get_field_schema(flat=True)` to discover which boolean flag fields were added by the quality plugin — never hardcode field names.

Example (adapt field names from schema):
```python
# Python SDK guidance — adapt field names from your schema
from fiftyone import ViewField as F

# Discover which quality flag fields exist via get_field_schema()
# then build the filter expression from those fields only
quality_filters = (F("blurry") == False) & (F("low_contrast") == False)

# Add uniqueness filter if computed
if "uniqueness" in field_schema:
    quality_filters = quality_filters & (F("uniqueness") >= 0.3)  # tune threshold

clean_view = dataset.match(quality_filters)
dataset.save_view("clean_<dataset_name>", clean_view)
```

Then load in App:
```
execute_operator("@voxel51/operators/load_saved_view", params={"name": "clean_<dataset_name>"})
```

Report to user:
- Total samples before cleaning
- Samples removed per quality filter
- Final clean sample count and percentage

### Option A: Uniqueness-based diverse subset
```
list_operators(builtin_only=False)
get_operator_schema(operator_uri="@voxel51/brain/compute_uniqueness")
execute_operator(operator_uri="@voxel51/brain/compute_uniqueness", params={})
set_view(sort_by="uniqueness", reverse=True, limit=<N>)
tag_samples(["diverse"])
```

### Option B: Representativeness-based coreset
```
list_operators(builtin_only=False)
get_operator_schema(operator_uri="@voxel51/brain/compute_representativeness")
execute_operator(operator_uri="@voxel51/brain/compute_representativeness", params={})
set_view(sort_by="representativeness", reverse=True, limit=<N>)
tag_samples(["coreset"])
```

### Option C: Train/val/test splits
```
# Clear any existing split tags first
untag_samples(["train", "val", "test"])

# Python SDK guidance for user:
# import fiftyone.utils.random as four
# four.random_split(dataset, {"train": 0.70, "val": 0.15, "test": 0.15})
```

### Saving and cloning
```
# Python SDK guidance:
# dataset.save_view("curated_subset", view)
# view.clone(name="<dataset_name>_curated", persistent=True)
```

Full subset workflows in `SUBSET-CREATION.md`.

---

## Phase 8 — Data Q&A Interface

Answer natural language questions about the dataset using aggregation MCP tools.

**MCP tools:** `count_values`, `bounds`, `mean`, `std`, `distinct`, `histogram_values`, `dataset_summary`, `count_sample_tags`

### Question → Tool mapping

| User question | MCP tool |
|---------------|----------|
| "How many samples have no annotations?" | `set_view(exists=["<label_field>"])` then count |
| "What is the class distribution?" | `count_values("<label_field>.label")` |
| "What % of samples are night scenes?" | `count_values("<attribute_field>.label")` |
| "What is the average bbox size?" | `mean("<detections_field>.detections.bounding_box")` |
| "How many images are untagged?" | `count_sample_tags()` |
| "What is the resolution range?" | `bounds("metadata.width")` + `bounds("metadata.height")` |
| "How many duplicate samples were removed?" | `count_values("tags")` for relevant tag |
| "What brain runs have been computed?" | `dataset_summary()` |
| "How confident are the predictions?" | `histogram_values("<pred_field>.detections.confidence", bins=20)` |
| "Are there any corrupted files?" | `set_view(filters={"metadata": null})` |

Always adapt field paths from schema discovery — never assume field names exist.

---

## Insight Generation Pattern

After any significant computation, generate and share interactive insights. This pattern applies after every phase.

### Template

1. **Compute aggregations** on the results:
   ```
   bounds("<score_field>")
   histogram_values("<score_field>", bins=20)
   mean("<score_field>")
   ```

2. **Calculate counts** for notable subsets:
   ```
   # Use set_view to count samples above/below thresholds
   set_view(filters={"<flag_field>": True})
   # Note the count from the response
   ```

3. **Create named saved views** via Python SDK (present as guidance to user):
   ```python
   # Present as Python SDK guidance
   dataset.save_view("insight_<name>", <view_expression>)
   ```

4. **Load the view in App** using the load_saved_view operator:
   ```
   execute_operator("@voxel51/operators/load_saved_view", params={"name": "insight_<name>"})
   ```

5. **Present narrative insight** with counts and percentages:
   ```
   ## Insight: <Phase Name>

   Found <N> samples (<X%>) flagged as <issue>.

   Saved view "<insight_name>" is now loaded in the App.
   → Visit the FiftyOne App (use get_session_info() to get the URL) to inspect these samples.

   Would you like to:
   - Tag these samples as "<tag>"
   - Move to the next phase
   - Dig deeper into this finding
   ```

### Example: After uniqueness computation

```
## Insight: Dataset Redundancy

Uniqueness range: <min> → <max> (mean: <mean>)

Bottom 10% by uniqueness (<N> samples) = highly redundant images — visually similar to many others.
View "redundant_samples" is now loaded in the App.

Top 20% by uniqueness (<M> samples) = maximally diverse images — best candidates for a training subset.
View "most_unique" is now loaded in the App.

Next up: Image quality checks (Phase 2). Continue?
```

---

## Delegation Map

| Sub-task | Delegated skill |
|----------|----------------|
| Import dataset if none loaded | `fiftyone-dataset-import` |
| Near-duplicate detection | `fiftyone-find-duplicates` |
| Embedding visualization | `fiftyone-embeddings-visualization` |
| Predictions for mistakenness | `fiftyone-dataset-inference` |

---

## Production Patterns (Multimodal / Grouped Datasets)

### Grouped dataset curation
```python
# Select sensor slice before brain ops (Python SDK guidance)
rgb_view = dataset.select_group_slices(["rgb_center"])
dataset.save_view("rgb_view", rgb_view)

# Run brain ops on slice with sensor-prefixed keys
# fob.compute_similarity(rgb_view, model="clip-vit-base32-torch", brain_key="rgb_img_sim")
```

### Check if similarity index supports text search
```python
# Python SDK guidance
info = dataset.get_brain_info("rgb_img_sim")
supports_text = info.config.supports_prompts  # True for CLIP-based
```

### Always save after field mutations
```python
# Python SDK guidance
view.apply_model(model, "predictions")
view.save()  # critical — never skip
```

### Thumbnail generation for large datasets (> 10k samples)
```python
# Python SDK guidance — improves App performance
# foui.transform_images(view, size=(-1, 128), output_field="thumbnail_path", output_dir=...)
# dataset.app_config.media_fields = ["filepath", "thumbnail_path"]
# dataset.app_config.grid_media_field = "thumbnail_path"
# dataset.save()
```

### ViewField patterns for quality filters
```python
from fiftyone import ViewField as F

# Resolution
F("metadata.width") > min_width
F("metadata.height") > min_height

# Color channels
F("metadata.num_channels") == 3

# Aspect ratio filters
long_filter = F("metadata.width") > 2 * F("metadata.height")
tall_filter  = F("metadata.height") > 2 * F("metadata.width")
normal_aspect = (~long_filter) & (~tall_filter)

# BBox area (relative)
rel_bbox_area = F("bounding_box")[2] * F("bounding_box")[3]

# Annotation quality (after mistakenness computation)
F("mistakenness") > 0.95
F("possible_missing") > 0
F("max_iou") > 0.75
```

---

## Reference Files

- `QUALITY-CHECKS.md` — Image quality filtering: metadata, blur, brightness, resolution, aspect ratio, CLIPScore
- `ANNOTATION-AUDIT.md` — Annotation error detection: mistakenness, hardness, IoU dedup, side-by-side review
- `SUBSET-CREATION.md` — Subset and split workflows: coreset, uniqueness, random split, saved views, cloning

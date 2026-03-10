# Curated Subset Creation & Splits

Workflow for creating curated subsets, building train/val/test splits, saving named views, and cloning datasets in FiftyOne. All field references are discovered dynamically — never hardcoded.

---

## Overview

Subset creation options (choose one or combine):

| Method | Best for |
|--------|----------|
| Semantic text search (CLIP) | Finding domain-specific subsets (e.g., "foggy day", "night scene") |
| Uniqueness-based subset | Maximum diversity — training set augmentation |
| Representativeness-based coreset | Minimum representative set — fast iteration / labeling budget |
| Random split | Standard train/val/test with reproducibility |
| Uniqueness-balanced split | Diverse val/test, representative train |
| Tag-based filtering | Working with pre-existing tags from earlier phases |

---

## Prerequisites

Before any subset creation:

```
dataset_summary()
get_field_schema(flat=True)
count_values("tags")
```

Check existing tags. If split tags (`train`, `val`, `test`) already exist, offer to clear them before creating new splits.

Also check what quality flag fields exist from Phase 2 — these are used to build the clean view:
```
get_field_schema(flat=True)
```

---

## 0. Build the Clean View First

Before creating subsets or splits, build a clean view that excludes quality-flagged samples. This should always be done before any other subset creation.

**Discover the quality flag fields from schema** — do not hardcode. Run `get_field_schema(flat=True)` and look for boolean fields added by the quality plugin (e.g., `blurry`, `low_contrast`, `low_saturation`, `weird_aspect_ratio`).

```python
# Python SDK guidance — adapt field names from your get_field_schema() output
from fiftyone import ViewField as F

# Build filter from discovered boolean flag fields
# Only include fields that actually exist in the schema
quality_filters = (F("blurry") == False)  # start with confirmed fields

# Add others if they exist in schema:
# quality_filters = quality_filters & (F("low_contrast") == False)
# quality_filters = quality_filters & (F("low_saturation") == False)
# quality_filters = quality_filters & (F("weird_aspect_ratio") == False)

# Add uniqueness filter if computed (tune threshold to dataset)
# quality_filters = quality_filters & (F("uniqueness") >= 0.3)

clean_view = dataset.match(quality_filters)

# Save with descriptive name
dataset.save_view("clean_training_set", clean_view)
```

Load in App for user to confirm:
```
execute_operator("@voxel51/operators/load_saved_view", params={"name": "clean_training_set"})
```

Report:
```
Clean view: <N> samples (<X%> of original <total>)
Removed:
  - <quality_flag_field>: <n> samples   (repeat for each flag field in schema)
  - low uniqueness (below threshold): <n> samples
```

Ask user to confirm the clean view before proceeding to splits.

---

## 1. Semantic Text Search Subsets (CLIP)

**Requires:** CLIP similarity index (from Phase 5 of SKILL.md). Check `dataset_summary()` for existing brain runs.

### Workflow

```
list_operators(builtin_only=False)
get_operator_schema(operator_uri="@voxel51/brain/sort_by_similarity")
```

For each semantic category to extract:
```
execute_operator(
    operator_uri="@voxel51/brain/sort_by_similarity",
    params={"query": "<text description>", "k": <N>, "brain_key": "<sim_key>"}
)
tag_samples(["<category_tag>"])
```

### Example queries (adapt to dataset domain)

```
"foggy day"        → tag_samples(["foggy"])
"night scene"      → tag_samples(["night"])
"rainy weather"    → tag_samples(["rainy"])
"crowded scene"    → tag_samples(["crowded"])
"edge case"        → tag_samples(["edge_case"])
"small objects"    → tag_samples(["small_objects"])
```

Confirm with user the query text and k value before tagging.

**Note:** Check that the similarity index supports text prompts before attempting text search:
```python
# Python SDK guidance
info = dataset.get_brain_info("<sim_key>")
supports_text = info.config.supports_prompts  # True for CLIP-based
```

---

## 2. Diverse Subset via Uniqueness

**Operator:** `@voxel51/brain/compute_uniqueness`

Selects samples that are maximally different from each other — best for training set diversity.

### Step 1: Compute uniqueness

```
list_operators(builtin_only=False)
get_operator_schema(operator_uri="@voxel51/brain/compute_uniqueness")
execute_operator(
    operator_uri="@voxel51/brain/compute_uniqueness",
    params={"uniqueness_field": "uniqueness"}
)
```

### Step 2: Sort and tag top-N unique samples

Ask user for desired subset size N, then:
```
set_view(sort_by="uniqueness", reverse=True, limit=<N>)
tag_samples(["diverse"])
```

### Step 3: Review in App

Direct user to the FiftyOne App (use get_session_info() to get the URL) to inspect the diverse subset before finalizing.

### Use case

- Creating a maximally diverse training set from a large pool
- Selecting diverse representative examples for active learning
- Building a challenging test set

---

## 3. Coreset via Representativeness

**Operator:** `@voxel51/brain/compute_representativeness`

Selects samples that best represent the full dataset distribution — best for labeling budget optimization.

### Step 1: Compute representativeness

```
list_operators(builtin_only=False)
get_operator_schema(operator_uri="@voxel51/brain/compute_representativeness")
execute_operator(
    operator_uri="@voxel51/brain/compute_representativeness",
    params={"representativeness_field": "representativeness"}
)
```

### Step 2: Sort and tag top-N representative samples

Ask user for coreset size N, then:
```
set_view(sort_by="representativeness", reverse=True, limit=<N>)
tag_samples(["coreset"])
```

### Use case

- Creating a minimal labeled set that represents the full data distribution
- Reducing annotation costs while preserving coverage
- Bootstrapping a model with a small but representative training set

---

## 4. Train/Val/Test Splits

### Option A: Random split (recommended for most cases)

**Always clear existing split tags first:**
```
untag_samples(["train", "val", "test"])
```

Then apply random split:
```python
# Python SDK guidance
import fiftyone.utils.random as four

four.random_split(
    dataset,
    {"train": 0.70, "val": 0.15, "test": 0.15},
    seed=5151   # use seed for reproducibility
)
```

Confirm the split ratios with user before running.

### Option B: Uniqueness-balanced split (recommended for detection/rare-class datasets)

Creates a diverse, hard test set while keeping representative samples for training.

```python
# Python SDK guidance

# 1. Compute uniqueness (if not already done in Phase 7)
# fob.compute_uniqueness(dataset)

# 2. Sort by uniqueness descending
unique_view = dataset.sort_by("uniqueness", reverse=True)

# 3. Take top-N as test set (diverse and challenging)
n_test = int(0.15 * len(dataset))
n_val  = int(0.15 * len(dataset))
test_ids = unique_view.head(n_test).values("id")
val_ids  = unique_view.skip(n_test).head(n_val).values("id")

# 4. Tag splits
dataset.select(test_ids).tag_samples(["test"])
dataset.select(val_ids).tag_samples(["val"])
dataset.match_tags(["test", "val"], bool=False).tag_samples(["train"])
```

### Option C: Semantic split (for domain-specific validation)

Use text search (CLIP) to put domain-specific scenarios in val/test:
```
list_operators(builtin_only=False)
get_operator_schema(operator_uri="@voxel51/brain/sort_by_similarity")

# Tag night scenes for val/test
execute_operator(
    operator_uri="@voxel51/brain/sort_by_similarity",
    params={"query": "night scene", "k": <N>, "brain_key": "<sim_key>"}
)
tag_samples(["val"])

# Tag foggy scenes for val/test
execute_operator(
    operator_uri="@voxel51/brain/sort_by_similarity",
    params={"query": "foggy conditions", "k": <N>, "brain_key": "<sim_key>"}
)
tag_samples(["val"])

# Tag remaining as train — confirm with user before running
# Python SDK: dataset.match_tags(["val", "test"], bool=False).tag_samples(["train"])
```

### Viewing splits

After tagging:
```
count_values("tags")
```

To work with split views:
```python
# Python SDK guidance
train_view = dataset.match_tags(["train"])
val_view   = dataset.match_tags(["val"])
test_view  = dataset.match_tags(["test"])
```

### Resplit pattern (clear and redo)

```
untag_samples(["train", "val", "test"])   # always clear before resplit
# then re-apply chosen split option above
```

---

## 5. Saving Named Views

Save views for team collaboration so others can load them without recomputing filters.

```python
# Python SDK guidance

# Save a view
dataset.save_view("curated_subset", curated_view)
dataset.save_view("train_split", train_view)
dataset.save_view("val_split", val_view)
dataset.save_view("test_split", test_view)
dataset.save_view("annotation_review", review_view)

# List all saved views
dataset.list_saved_views()

# Load a saved view
view = dataset.load_saved_view("curated_subset")
```

Suggest saving named views at the end of each phase so results are preserved and shareable.

---

## 6. Cloning to a New Dataset

Clone the curated subset to a new persistent dataset. This creates an independent copy with all brain runs and saved views.

Confirm with user before cloning:
- New dataset name
- Whether to include all brain runs

```python
# Python SDK guidance

# Clone from a view
curated_dataset = curated_view.clone(
    name=f"{dataset.name}_curated",
    persistent=True
)

# Or clone from a tag-matched view
train_dataset = dataset.match_tags(["train"]).clone(
    name=f"{dataset.name}_train",
    persistent=True
)
```

After cloning, verify:
```
list_datasets()
set_context(dataset_name="<new_dataset_name>")
dataset_summary()
```

---

## 7. Exporting Splits (for Training Pipelines)

After splits are tagged, export each split to the target training format.

**Delegate to `fiftyone-dataset-export` skill** for this step.

Common export patterns (via that skill):
```python
# Python SDK guidance — use fiftyone-dataset-export skill for MCP version

# YOLO format
train_view.export(
    export_dir="./exports/yolo/train",
    dataset_type=fo.types.YOLOv5Dataset,
    label_field="<ground_truth_field>"   # from schema discovery
)

# COCO format
val_view.export(
    export_dir="./exports/coco/val",
    dataset_type=fo.types.COCODetectionDataset,
    label_field="<ground_truth_field>"
)
```

---

## 8. Patch-Level Object Curation (Detection Datasets)

For detection datasets, operate at the object level rather than image level.

### Prerequisites

- Detections field exists (confirmed from schema in Phase 1)
- CLIP similarity index computed at patch level (Phase 5)

### Workflow

```
list_operators(builtin_only=False)
get_operator_schema(operator_uri="@voxel51/brain/compute_visualization")
execute_operator(
    operator_uri="@voxel51/brain/compute_visualization",
    params={
        "patches_field": "<detections_field>",   # from schema discovery
        "model": "clip-vit-base32-torch",
        "method": "umap",
        "num_dims": 2,                           # REQUIRED — operator fails without this
        "brain_key": "<detections_field>_clip_umap"
    },
    delegate=True
)
```

In the App Embeddings panel:
- Switch to "Patches" mode
- Each point = one object instance
- Lasso-select clusters of objects → tag at object level
- Find object-level outliers (rare objects, badly annotated objects)

### Object-level tagging

```python
# Python SDK guidance
# After lasso-selecting in App, tag the patch view:
patches_view = dataset.to_patches("<detections_field>")
# ... filter patches ...
# patches_view.tag_labels(["outlier_object"])
```

---

## Subset Creation Decision Guide

```
Is there a large pool of unannotated data?
  → Use compute_representativeness coreset to select what to annotate

Do you need a maximally diverse training set?
  → Use compute_uniqueness → sort desc → take top-N

Do you need a challenging test set?
  → Use uniqueness-balanced split (diverse test) or semantic text search for edge cases

Do you have a labeling budget constraint?
  → Use coreset (representativeness) to maximize coverage per labeled sample

Do you need standard reproducible splits?
  → Use four.random_split with seed=5151

Do you need to curate specific domain scenarios?
  → Use CLIP text search to extract semantic subsets
```

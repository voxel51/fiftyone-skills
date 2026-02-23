# Recipe Templates

## Contents
- [Canonical Structure](#canonical-structure)
- [Key Differences from Other Types](#key-differences-from-other-types)
- [Recipe: Export Dataset to COCO Format](#recipe-export-dataset-to-coco-format)
- [Recipe: Remove Duplicate Images](#recipe-remove-duplicate-images)
- [Recipe: Filter Low-Confidence Detections](#recipe-filter-low-confidence-detections)
- [Recipe: Compare Two Models Side by Side](#recipe-compare-two-models-side-by-side)
- [Recipe: Compute and Visualize Embeddings](#recipe-compute-and-visualize-embeddings)
- [Recipe: Merge Two Datasets](#recipe-merge-two-datasets)
- [Recipe: Add Custom Metadata to Samples](#recipe-add-custom-metadata-to-samples)
- [Adaptation Guidelines](#adaptation-guidelines)

---

**Target audience:** Practitioners who know FiftyOne and need a quick solution
**Duration:** 5-10 minutes
**Cell count:** 6-10 cells
**Scope:** Solve one specific problem, minimal explanation

The recipes below are **structural examples** — follow the canonical structure but adapt the specific operations, field names, and parameters to the user's request. Fetch `https://docs.voxel51.com/llms.txt` for the correct API for any task.

## Canonical Structure

| Cell | Type | Content |
|---|---|---|
| 0 | markdown | Title (verb phrase) + one sentence description |
| 1 | code | pip install (if needed) + all imports in one cell |
| 2 | code | Load or create data |
| 3 | markdown | Brief explanation of approach (2-3 sentences max) |
| 4 | code | Core solution |
| 5 | code | Verify result |
| 6 | markdown | Variations (2-4 bullet points with alternative approaches) |

## Key Differences from Other Types

- **No learning goals section** — the title tells you what you get
- **Minimal markdown** — just enough to understand the approach
- **Imports + pip in one cell** — get to the solution fast
- **Variations at the end** — show related approaches as bullet points, not full cells
- **No App visualization required** — include only if relevant to the recipe

## Recipe: Export Dataset to COCO Format

### Cell 0 — markdown
```markdown
# Export a FiftyOne Dataset to COCO Format

Export any FiftyOne dataset with detection labels to the COCO JSON format,
ready for training or sharing.
```

### Cell 1 — code
```python
import fiftyone as fo
import fiftyone.types as fot
```

### Cell 2 — code
```python
# Load your dataset (replace with your dataset name)
dataset = fo.load_dataset("my-dataset")
print(dataset)
```

### Cell 3 — markdown
```markdown
FiftyOne's `export()` method converts datasets to standard formats. For COCO,
this creates the `labels.json` file and copies images to the export directory.
```

### Cell 4 — code
```python
dataset.export(
    export_dir="/tmp/coco-export",
    dataset_type=fot.COCODetectionDataset,
    label_field="ground_truth",
)
```

### Cell 5 — code
```python
import os

export_dir = "/tmp/coco-export"
print(f"Exported files:")
for f in os.listdir(export_dir):
    path = os.path.join(export_dir, f)
    if os.path.isdir(path):
        print(f"  {f}/ ({len(os.listdir(path))} files)")
    else:
        print(f"  {f}")
```

### Cell 6 — markdown
```markdown
**Variations:**
- Export only labels (no images): `dataset.export(..., export_media=False)`
- Export a filtered view: `view = dataset.match(F("tag") == "train"); view.export(...)`
- Export to YOLO format: `dataset_type=fot.YOLOv5Dataset`
- Export to VOC format: `dataset_type=fot.VOCDetectionDataset`
```

---

## Recipe: Remove Duplicate Images

### Cell 0 — markdown
```markdown
# Remove Duplicate Images from a Dataset

Find and remove exact or near-duplicate images using FiftyOne's brain methods.
```

### Cell 1 — code
```python
import fiftyone as fo
import fiftyone.brain as fob
```

### Cell 2 — code
```python
dataset = fo.load_dataset("my-dataset")
print(f"Samples before dedup: {len(dataset)}")
```

### Cell 3 — markdown
```markdown
Compute image embeddings and find near-duplicates within a distance threshold.
Lower thresholds are stricter (closer to exact match).
```

### Cell 4 — code
```python
# Compute similarity index
fob.compute_similarity(dataset, brain_key="sim", model="clip-vit-base32-torch")

# Find near-duplicates (threshold 0.3 = visually similar)
results = fob.compute_near_duplicates(dataset, brain_key="sim", thresh=0.3)
print(f"Found {len(results.near_duplicates)} near-duplicate groups")
```

### Cell 5 — code
```python
# Remove duplicates, keeping one from each group
dups = results.duplicates_view()
dataset.delete_samples(dups)
print(f"Samples after dedup: {len(dataset)}")
```

### Cell 6 — markdown
```markdown
**Variations:**
- Find exact duplicates only: `fob.compute_exact_duplicates(dataset)`
- Adjust threshold: `thresh=0.1` (stricter) or `thresh=0.5` (more permissive)
- Review before deleting: `session = fo.launch_app(dups)` to inspect flagged images
- Use DINOv2 for visual-only similarity: `model="dinov2-vits14-torch"`
```

---

## Recipe: Filter Low-Confidence Detections

### Cell 0 — markdown
```markdown
# Filter Low-Confidence Detections

Remove predictions below a confidence threshold from your dataset's detection field.
```

### Cell 1 — code
```python
import fiftyone as fo
from fiftyone import ViewField as F
```

### Cell 2 — code
```python
dataset = fo.load_dataset("my-dataset")
print(f"Total detections: {dataset.count('predictions.detections')}")
```

### Cell 3 — markdown
```markdown
Use `filter_labels()` to keep only detections above a confidence threshold.
This creates a view — the underlying data is not modified.
```

### Cell 4 — code
```python
# Keep only detections with confidence >= 0.5
high_conf_view = dataset.filter_labels(
    "predictions", F("confidence") >= 0.5
)
print(f"Detections after filtering: {high_conf_view.count('predictions.detections')}")
```

### Cell 5 — code
```python
# To permanently remove low-confidence detections, save the filtered view
high_conf_view.save("predictions")
print(f"Saved. Detections: {dataset.count('predictions.detections')}")
```

### Cell 6 — markdown
```markdown
**Variations:**
- Filter by class: `F("label") == "person"`
- Combine filters: `(F("confidence") >= 0.5) & (F("label").is_in(["person", "car"]))`
- View as a temporary filter (no save): use the view directly in the App
```

---

## Recipe: Compare Two Models Side by Side

### Cell 0 — markdown
```markdown
# Compare Two Models Side by Side

Run two detection models on the same dataset and compare their predictions
using evaluation metrics.
```

### Cell 1 — code
```python
import fiftyone as fo
import fiftyone.zoo as foz
```

### Cell 2 — code
```python
dataset = fo.load_dataset("my-dataset")
print(dataset)
```

### Cell 3 — markdown
```markdown
Apply two models with different label fields, then evaluate each against
ground truth to compare metrics.
```

### Cell 4 — code
```python
# Run Model A
model_a = foz.load_zoo_model("yolov8n-coco-torch")
dataset.apply_model(model_a, label_field="model_a")

# Run Model B
model_b = foz.load_zoo_model("yolov8m-coco-torch")
dataset.apply_model(model_b, label_field="model_b")
```

### Cell 5 — code
```python
# Evaluate both
results_a = dataset.evaluate_detections("model_a", gt_field="ground_truth", eval_key="eval_a", method="coco", compute_mAP=True)
results_b = dataset.evaluate_detections("model_b", gt_field="ground_truth", eval_key="eval_b", method="coco", compute_mAP=True)

print(f"Model A (YOLOv8n) mAP: {results_a.mAP():.3f}")
print(f"Model B (YOLOv8m) mAP: {results_b.mAP():.3f}")
```

### Cell 6 — markdown
```markdown
**Variations:**
- Compare different model families: Faster R-CNN vs YOLO
- Compare at different IoU thresholds: `iou=0.25` vs `iou=0.75`
- View samples where models disagree: filter by different TP/FP counts
```

---

## Recipe: Compute and Visualize Embeddings

### Cell 0 — markdown
```markdown
# Compute and Visualize Image Embeddings

Compute image embeddings and visualize your dataset in 2D using UMAP.
```

### Cell 1 — code
```python
import fiftyone as fo
import fiftyone.brain as fob
```

### Cell 2 — code
```python
dataset = fo.load_dataset("my-dataset")
print(dataset)
```

### Cell 3 — markdown
```markdown
Compute CLIP embeddings and reduce to 2D with UMAP for visualization
in the FiftyOne App Embeddings panel.
```

### Cell 4 — code
```python
fob.compute_similarity(dataset, brain_key="sim", model="clip-vit-base32-torch")
fob.compute_visualization(dataset, brain_key="viz", method="umap")
```

### Cell 5 — code
```python
session = fo.launch_app(dataset)
# Open the Embeddings panel in the App to explore the 2D visualization
```

### Cell 6 — markdown
```markdown
**Variations:**
- Use DINOv2 for visual-only similarity: `model="dinov2-vits14-torch"`
- Use t-SNE instead of UMAP: `method="tsne"`
- Color by field in the Embeddings panel: select a label field in the dropdown
- Compute uniqueness scores: `fob.compute_uniqueness(dataset)`
```

---

## Recipe: Merge Two Datasets

### Cell 0 — markdown
```markdown
# Merge Two FiftyOne Datasets

Combine samples from two datasets into a single dataset.
```

### Cell 1 — code
```python
import fiftyone as fo
```

### Cell 2 — code
```python
dataset_a = fo.load_dataset("dataset-a")
dataset_b = fo.load_dataset("dataset-b")
print(f"Dataset A: {len(dataset_a)} samples")
print(f"Dataset B: {len(dataset_b)} samples")
```

### Cell 3 — markdown
```markdown
Use `merge_samples()` to combine datasets. Samples with matching filepaths
will be merged (their labels combined); new samples will be added.
```

### Cell 4 — code
```python
dataset_a.merge_samples(dataset_b)
print(f"Merged dataset: {len(dataset_a)} samples")
```

### Cell 5 — markdown
```markdown
**Variations:**
- Create a new merged dataset: `merged = fo.Dataset("merged"); merged.merge_samples(dataset_a); merged.merge_samples(dataset_b)`
- Merge only specific fields: `dataset_a.merge_samples(dataset_b, fields=["ground_truth"])`
- Skip existing: `dataset_a.merge_samples(dataset_b, skip_existing=True)`
```

---

## Recipe: Add Custom Metadata to Samples

### Cell 0 — markdown
```markdown
# Add Custom Metadata to Samples

Add custom fields (scores, categories, tags) to your dataset samples
programmatically.
```

### Cell 1 — code
```python
import fiftyone as fo
```

### Cell 2 — code
```python
dataset = fo.load_dataset("my-dataset")
print(dataset)
```

### Cell 3 — markdown
```markdown
FiftyOne samples support dynamic fields. Set any attribute on a sample
and call `sample.save()` to persist it.
```

### Cell 4 — code
```python
# Add a custom field to all samples
for sample in dataset:
    sample["quality_score"] = len(sample.filepath)  # placeholder logic
    sample["source"] = "batch_1"
    sample.save()

print(dataset.count_values("source"))
```

### Cell 5 — markdown
```markdown
**Variations:**
- Bulk set with `set_values()`: `dataset.set_values("field", values_list)`
- Tag samples: `dataset.tag_samples("my-tag")`
- Add computed fields: use `dataset.apply_model()` or brain methods
- Delete a field: `dataset.delete_sample_field("field_name")`
```

## Adaptation Guidelines

When creating a new recipe:

1. **Title must be a verb phrase** — "Export...", "Filter...", "Compute...", "Remove..."
2. **One sentence description** — what it does and when to use it
3. **Get to the code fast** — imports + data in the first 2 cells
4. **Core solution in one cell** — the main code block should be copy-pasteable
5. **End with variations** — bullet points showing related approaches
6. **No App visualization unless essential** — recipes are about code, not exploration
7. **Keep it under 10 cells** — if it needs more, it's a tutorial, not a recipe

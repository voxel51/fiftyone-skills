# Notebook Structure Patterns

## Contents
- [Cell Rules](#cell-rules)
- [Pipeline Stage Cell Templates](#pipeline-stage-cell-templates)
- [Narrative Flow Guidelines](#narrative-flow-guidelines)

---

This document defines the **cell structure** for each pipeline stage. It tells you HOW to structure cells and WHERE to find code patterns — without duplicating code that already exists in other skills and documentation.

## Cell Rules

1. **Every code cell MUST be preceded by a markdown cell** that explains what and why
2. **Markdown cells** should explain the purpose, not just describe the code
3. **Code cells** should be under 15 lines, one concept per cell
4. **First cell** is always a markdown title + description
5. **Last code cell** is always cleanup (delete temporary datasets, close sessions)
6. **Include `print()` calls** so users see output when running the notebook

## Pipeline Stage Cell Templates

### 1. Setup Section (3 cells)

| Cell | Type | Content Pattern |
|---|---|---|
| N | code | `!pip install fiftyone [extras]` — preceded by previous section's markdown. Only include packages actually used (e.g., `ultralytics` for YOLO, `umap-learn` for UMAP) |
| N+1 | markdown | `## Setup` + brief explanation of what libraries are used and why |
| N+2 | code | All imports in one cell, following FiftyOne conventions |

**Import cell pattern:**
```python
import fiftyone as fo
import fiftyone.zoo as foz
# Add only what the notebook actually uses:
# import fiftyone.brain as fob      # if using brain methods
# import fiftyone.types as fot      # if exporting
# from fiftyone import ViewField as F  # if filtering
```

**Code pattern source:** See SKILL.md "Code Pattern Sources" table for related skills. Fetch `https://docs.voxel51.com/llms.txt` for current API.

### 2. Data Loading Section (2 cells)

| Cell | Type | Content Pattern |
|---|---|---|
| N | markdown | `## Load Dataset` + explain what dataset, why it's a good choice, what it contains |
| N+1 | code | Load dataset + `print(dataset)` + `print(dataset.first())` in one cell |

**Zoo dataset pattern:**
```python
dataset = foz.load_zoo_dataset(
    "dataset-name",
    split="validation",
    max_samples=200,
    seed=51,
    dataset_name="notebook-name",
)
print(dataset)
```

**Code pattern source:** Fetch `https://docs.voxel51.com/llms.txt` for all dataset loading methods.

### 3. Exploration Section (3-4 cells)

| Cell | Type | Content Pattern |
|---|---|---|
| N | markdown | `## Explore the Dataset` + explain the value of visual exploration |
| N+1 | code | `session = fo.launch_app(dataset)` |
| N+2 | markdown | Brief note about what to look for in the App |
| N+3 | code | Statistics: `count_values()`, `distinct()`, `bounds()`, sorting |

**Statistics patterns:**
```python
# Class distribution
counts = dataset.count_values("field.detections.label")
print(dict(sorted(counts.items(), key=lambda x: -x[1])[:10]))

# Dataset overview
print(f"Samples: {len(dataset)}")
print(f"Classes: {dataset.distinct('field.detections.label')}")
```

**Code pattern source:** Fetch `https://docs.voxel51.com/llms.txt` for aggregation methods (count_values, distinct, bounds, mean, std, histogram_values).

### 4. Brain Methods Section (2-4 cells)

| Cell | Type | Content Pattern |
|---|---|---|
| N | markdown | `## [Brain Method Name]` + explain what it does and why it's useful |
| N+1 | code | Compute brain method + view results (merge related operations) |
| N+2 | markdown | (Optional) Explain next analysis step |
| N+3 | code | (Optional) Additional analysis or filtering |

**Brain method patterns use the Python SDK directly in notebooks:**
```python
import fiftyone.brain as fob

# Compute similarity (creates embeddings index)
fob.compute_similarity(dataset, brain_key="sim", model="clip-vit-base32-torch")

# Compute visualization (UMAP/t-SNE)
fob.compute_visualization(dataset, brain_key="viz", method="umap")

# Compute uniqueness (outlier scoring)
fob.compute_uniqueness(dataset, uniqueness_field="uniqueness")
```

**Code pattern source:** Fetch `https://docs.voxel51.com/llms.txt` for brain methods.

### 5. Inference Section (2 cells)

| Cell | Type | Content Pattern |
|---|---|---|
| N | markdown | `## Run Model Inference` + explain what model does and why this one was chosen |
| N+1 | code | Load model + apply to dataset + view predictions (`session.view = dataset.view()`) |

**Inference pattern:**
```python
model = foz.load_zoo_model("model-name")
dataset.apply_model(model, label_field="predictions")
print(dataset)
```

**Common models by task** (not exhaustive — fetch `https://docs.voxel51.com/llms.txt` for full model zoo):
- Detection: `yolov8n-coco-torch`, `faster-rcnn-resnet50-fpn-coco-torch`
- Classification: `resnet50-imagenet-torch`, `mobilenet-v2-imagenet-torch`
- Segmentation: `deeplabv3-resnet101-coco-torch`, `sam-vit-base-torch`
- Embeddings: `clip-vit-base32-torch`, `dinov2-vits14-torch`

### 6. Evaluation Section (4 cells)

| Cell | Type | Content Pattern |
|---|---|---|
| N | markdown | `## Evaluate Predictions` + explain evaluation methodology |
| N+1 | code | Run evaluation + print report (+ confusion matrix if relevant) |
| N+2 | markdown | `## Analyze Errors` + explain TP/FP/FN concept |
| N+3 | code | Evaluation patches view + filter to errors |

**Evaluation pattern:**
```python
results = dataset.evaluate_detections(
    "predictions",
    gt_field="ground_truth",
    eval_key="eval",
    method="coco",
    compute_mAP=True,
)
results.print_report()
print(f"mAP: {results.mAP():.3f}")
```

**Patches pattern:**
```python
patches = dataset.to_evaluation_patches("eval")
print(patches.count_values("type"))

fp_view = patches.match(F("type") == "fp")
session.view = fp_view
```

**Evaluation methods by label type:**
- `Detections` → `dataset.evaluate_detections()` (methods: "coco", "open-images")
- `Classification` → `dataset.evaluate_classifications()` (methods: "simple", "top-k", "binary")
- `Segmentation` → `dataset.evaluate_segmentations()` (methods: "simple")
- `Regression` → `dataset.evaluate_regressions()` (methods: "simple")

**Code pattern source:** Fetch `https://docs.voxel51.com/llms.txt` for evaluation API.

### 7. Export Section (2 cells)

| Cell | Type | Content Pattern |
|---|---|---|
| N | markdown | `## Export Dataset` + explain the target format and why |
| N+1 | code | Export call |

**Export pattern:**
```python
import fiftyone.types as fot

dataset.export(
    export_dir="/tmp/export-dir",
    dataset_type=fot.COCODetectionDataset,
    label_field="ground_truth",
)
```

**Common export types:**
- `fot.COCODetectionDataset` - COCO JSON format
- `fot.YOLOv5Dataset` - YOLOv5 format
- `fot.VOCDetectionDataset` - Pascal VOC XML
- `fot.CVATImageDataset` - CVAT format
- `fot.CSVDataset` - CSV

**Code pattern source:** Fetch `https://docs.voxel51.com/llms.txt` for export types.

### 8. Conclusion Section (2 cells)

| Cell | Type | Content Pattern |
|---|---|---|
| N | markdown | `## Conclusion` + summary of what was covered, key takeaways, next steps with links |
| N+1 | code | Cleanup: `fo.delete_dataset("dataset-name")` |

**Conclusion markdown pattern:**
```markdown
## Conclusion

In this notebook, you learned how to:
- [Bullet point for each major section]

**Next Steps:**
- [Link to related tutorial](https://docs.voxel51.com/tutorials/...)
- [Link to relevant docs](https://docs.voxel51.com/user_guide/...)
- [Link to FiftyOne community](https://discord.gg/fiftyone-community)
```

## Narrative Flow Guidelines

### Getting Started Notebooks
- **Tone:** Welcoming, encouraging, no jargon without explanation
- **Pacing:** Slow, one concept at a time
- **Markdown:** Explain every concept as if the reader is new to FiftyOne
- **App guidance:** Tell users what to look for in the App ("Notice how the bounding boxes...")

### Tutorial Notebooks
- **Tone:** Technical but accessible, assumes basic FiftyOne knowledge
- **Pacing:** Moderate, can combine related concepts
- **Markdown:** Explain the "why" behind each technique, include real-world motivation
- **Analysis:** Include interpretation of results ("The high number of false positives suggests...")

### Recipe Notebooks
- **Tone:** Direct, concise, no preamble
- **Pacing:** Fast, get to the solution quickly
- **Markdown:** Minimal explanation, focus on the code
- **Variations:** End with alternative approaches as bullet points

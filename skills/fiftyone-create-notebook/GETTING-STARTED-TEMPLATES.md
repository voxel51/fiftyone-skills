# Getting Started Templates

## Contents
- [Canonical Structure](#canonical-structure)
- [Template: Object Detection](#template-object-detection)
- [Template: Image Classification](#template-image-classification)
- [Template: Image Similarity & Embeddings](#template-image-similarity--embeddings)
- [Adaptation Guidelines](#adaptation-guidelines)
- [Guide Packaging](#guide-packaging)

---

**Target audience:** Beginners new to FiftyOne
**Duration:** 15-30 minutes
**Cell count:** 15-22 cells
**Scope:** Full end-to-end pipeline for one domain

The templates below are **structural examples** — follow the canonical structure and cell patterns, but adapt the dataset, model, field names, and sections to the user's specific domain. Fetch `https://docs.voxel51.com/llms.txt` for the correct API for any domain.

## Canonical Structure

| Phase | Typical Cells | Content |
|---|---|---|
| Title | 0 | `# Getting Started with {Domain} in FiftyOne` + metadata + overview |
| Learning Goals | 1 | `## What You Will Learn` + bullet list of skills |
| Setup | 2-4 | pip install + setup markdown + imports |
| Load Data | 5-6 | Explain dataset + load from zoo + inspect |
| Explore | 7-10 | Launch App + what to look for + dataset statistics |
| Core Workflow | varies | Domain-specific: inference, brain methods, or analysis |
| Evaluate | varies | Evaluation + report + error analysis (if applicable) |
| Export | varies | Explain format + export (optional) |
| Conclusion | last 2 | Summary + next steps links + cleanup |

## Template: Object Detection

### Cell 0 — markdown
```markdown
# Getting Started with Object Detection in FiftyOne

**Level:** Beginner | **Time:** 20 minutes | **Prerequisites:** Basic Python

In this notebook, you will load an object detection dataset, explore it visually,
run a state-of-the-art detection model, evaluate its predictions against ground
truth annotations, and export the results. By the end, you will have a complete
understanding of the FiftyOne detection workflow.
```

### Cell 1 — markdown
```markdown
## What You Will Learn

- Load a detection dataset from the FiftyOne Dataset Zoo
- Explore images and annotations in the FiftyOne App
- Run YOLOv8 object detection on your dataset
- Evaluate predictions using COCO-style metrics (mAP, precision, recall)
- Analyze false positives and false negatives with evaluation patches
- Export your dataset to YOLO format for training
```

### Cell 2 — code
```python
!pip install -q fiftyone ultralytics
```

### Cell 3 — markdown
```markdown
## Setup

Import the libraries we will use throughout this notebook.
```

### Cell 4 — code
```python
import fiftyone as fo
import fiftyone.zoo as foz
from fiftyone import ViewField as F
```

### Cell 5 — markdown
```markdown
## Load the Dataset

We will use a subset of the [COCO 2017](https://cocodataset.org/) validation set.
COCO is one of the most widely used benchmarks for object detection, containing
80 object categories with bounding box annotations.

We load 200 samples to keep things fast while still being representative.
```

### Cell 6 — code
```python
dataset = foz.load_zoo_dataset(
    "coco-2017",
    split="validation",
    max_samples=200,
    seed=51,
    dataset_name="detection-getting-started",
)

print(dataset)

# Inspect a single sample to understand the data structure
print(dataset.first())
```

### Cell 7 — markdown
```markdown
## Explore in the FiftyOne App

Launch the FiftyOne App to visually browse images and their annotations.
Click on any image to see its bounding boxes and labels.
```

### Cell 8 — code
```python
session = fo.launch_app(dataset)
```

### Cell 9 — markdown
```markdown
## Understand the Data

Let's look at the class distribution to understand what objects appear
most frequently in our dataset.
```

### Cell 10 — code
```python
# Count detections per class
counts = dataset.count_values("ground_truth.detections.label")
top_classes = dict(sorted(counts.items(), key=lambda x: -x[1])[:15])
print("Top 15 classes by detection count:")
for cls, count in top_classes.items():
    print(f"  {cls}: {count}")
```

### Cell 11 — markdown
```markdown
## Run Object Detection

Now let's run a YOLOv8 model to generate predictions and compare them
against the ground truth annotations. YOLOv8-small balances speed and
accuracy well for this demonstration.
```

### Cell 12 — code
```python
model = foz.load_zoo_model("yolov8s-coco-torch")

dataset.apply_model(model, label_field="predictions")

print(dataset)

# Refresh the App to see predictions alongside ground truth
session.view = dataset.view()
```

### Cell 13 — markdown
```markdown
## Evaluate Predictions

Compare the model's predictions against the ground truth using
COCO-style evaluation. This computes mAP (mean Average Precision),
per-class precision and recall, and marks each prediction as a
true positive (TP), false positive (FP), or false negative (FN).
```

### Cell 14 — code
```python
results = dataset.evaluate_detections(
    "predictions",
    gt_field="ground_truth",
    eval_key="eval",
    method="coco",
    compute_mAP=True,
)

results.print_report(classes=["person", "car", "dog", "cat", "chair"])
print(f"\nmAP: {results.mAP():.3f}")
```

### Cell 15 — markdown
```markdown
## Analyze Errors

The evaluation patches view lets you examine individual true positives,
false positives, and false negatives. This is invaluable for understanding
where your model succeeds and fails.
```

### Cell 16 — code
```python
# Convert to evaluation patches
patches = dataset.to_evaluation_patches("eval")
print(patches.count_values("type"))

# View false positives in the App
fp_view = patches.match(F("type") == "fp")
session.view = fp_view
```

### Cell 17 — markdown
```markdown
## Export for Training

Export the dataset to YOLOv5 format, ready for fine-tuning or
training a custom model.
```

### Cell 18 — code
```python
import fiftyone.types as fot

dataset.export(
    export_dir="/tmp/detection-getting-started-export",
    dataset_type=fot.YOLOv5Dataset,
    label_field="ground_truth",
)

print("Exported to /tmp/detection-getting-started-export/")
```

### Cell 19 — markdown
```markdown
## Conclusion

In this notebook, you learned how to:

- **Load** a COCO detection dataset with `foz.load_zoo_dataset()`
- **Explore** data visually in the FiftyOne App
- **Run inference** with YOLOv8 using `dataset.apply_model()`
- **Evaluate** predictions with COCO metrics (`evaluate_detections`)
- **Analyze** TP/FP/FN with evaluation patches
- **Export** to YOLO format for training

**Next Steps:**
- [Embeddings Visualization](https://docs.voxel51.com/tutorials/image_embeddings.html) — Visualize your dataset in embedding space
- [Finding Annotation Mistakes](https://docs.voxel51.com/tutorials/detection_mistakes.html) — Use brain methods to find labeling errors
- [FiftyOne User Guide](https://docs.voxel51.com/user_guide/index.html) — Deep dive into FiftyOne capabilities
```

### Cell 20 — code
```python
# Cleanup
fo.delete_dataset("detection-getting-started")
```

---

## Template: Image Classification

| Cell | Type | Content |
|---|---|---|
| 0 | markdown | Title: `# Getting Started with Image Classification in FiftyOne` + metadata + overview |
| 1 | markdown | What You Will Learn: load CIFAR-10, explore class balance, run ResNet-50, evaluate, find errors |
| 2 | code | `!pip install -q fiftyone` |
| 3 | markdown | `## Setup` + import explanation |
| 4 | code | Imports: `fo`, `foz`, `F` |
| 5 | markdown | `## Load the Dataset` + explain CIFAR-10 (10 classes, 60K images) |
| 6 | code | `foz.load_zoo_dataset("cifar10", split="test", max_samples=500)` + `print(dataset)` |
| 7 | markdown | `## Explore in the FiftyOne App` |
| 8 | code | `session = fo.launch_app(dataset)` |
| 9 | markdown | `## Class Distribution` |
| 10 | code | `dataset.count_values("ground_truth.label")` |
| 11 | markdown | `## Run Classification` + explain ResNet-50 |
| 12 | code | Load `resnet50-imagenet-torch` + `dataset.apply_model(...)` + `session.view = dataset.view()` |
| 13 | markdown | `## Evaluate Predictions` |
| 14 | code | `dataset.evaluate_classifications(...)` + `results.print_report()` |
| 15 | markdown | `## Find Misclassified Images` |
| 16 | code | `dataset.match(F("eval") == False)` + `session.view` |
| 17 | markdown | `## Conclusion` + summary + next steps |
| 18 | code | `fo.delete_dataset("classification-getting-started")` |

---

## Template: Image Similarity & Embeddings

| Cell | Type | Content |
|---|---|---|
| 0 | markdown | Title: `# Getting Started with Image Similarity in FiftyOne` + metadata + overview |
| 1 | markdown | What You Will Learn: load quickstart, compute CLIP embeddings, UMAP visualization, find outliers |
| 2 | code | `!pip install -q fiftyone umap-learn` |
| 3 | markdown | `## Setup` + import explanation |
| 4 | code | Imports: `fo`, `foz`, `fob` |
| 5 | markdown | `## Load the Dataset` + explain quickstart dataset |
| 6 | code | `foz.load_zoo_dataset("quickstart")` + `print(dataset)` |
| 7 | markdown | `## Explore in the FiftyOne App` |
| 8 | code | `session = fo.launch_app(dataset)` |
| 9 | markdown | `## Compute Embeddings and Visualization` + explain CLIP + UMAP |
| 10 | code | `fob.compute_similarity(...)` + `fob.compute_visualization(...)` + `session.view` |
| 11 | markdown | `## Find Outliers with Uniqueness` + explain uniqueness scoring |
| 12 | code | `fob.compute_uniqueness(...)` + sort by uniqueness + `session.view` |
| 13 | markdown | `## Conclusion` + summary + next steps |
| 14 | code | `fo.delete_dataset("similarity-getting-started")` |

## Adaptation Guidelines

When creating a new getting-started notebook for a domain not listed above:

1. **Pick a zoo dataset** that represents the domain well
2. **Choose an appropriate model** from the Model Zoo
3. **Use the matching evaluation method** (detections → `evaluate_detections`, classifications → `evaluate_classifications`)
4. **Keep it under 22 cells** — brevity is key for beginners
5. **Explain every concept** as if the reader has never used FiftyOne
6. **Include App screenshots guidance** — tell users what to look for
7. **Include metadata** in the title cell: level, time estimate, prerequisites

## Guide Packaging

When creating a multi-notebook getting-started guide (not just a single notebook), follow this structure.

### Folder Structure

```
docs/source/getting_started/{guide_name}/
├── index.rst             # Landing page: title, video, objectives, prerequisites, toctree
├── summary.rst           # Recap, exercises, resources, feedback
├── requirements.txt      # Exact dependencies + Python version
├── 01_intro.ipynb        # Numbered, self-contained notebooks
├── 02_explore.ipynb
└── 03_evaluate.ipynb
```

### Notebook Requirements

- **Numbering:** `01_`, `02_`, `03_` — sequential, each independently runnable
- **Metadata** in title cell: level (Beginner/Intermediate/Advanced), time estimate, prerequisites, recommended reads
- **Images:** `.webp` format on CDN: `![name](https://cdn.voxel51.com/getting_started_{guide_name}/notebook{N}/{file}.webp)`
- **Upload:** `gsutil cp /path/to/file.webp gs://voxel51-static-cdn-91225dde9e4f2d89/getting_started_{guide_name}/notebook{N}/`
- **Dependencies:** exact versions in `requirements.txt`; don't import all libraries in the first notebook

### index.rst

Must include: title, short description, embedded video (optional), learning objectives, prerequisites, Python/library/OS versions, guide overview with linked steps, toctree with all notebooks + summary.

Example card for the global getting-started index:
```rst
.. customcarditem::
   :header: {Guide Name}
   :description: {Short description}
   :link: {guide_name}/index.html
   :image: ../_static/images/guides/{guide_name}.png
   :tags: vision, beginner
```

### summary.rst

Must include: congratulations message, step-by-step recap, suggested exercises, resources and further reading, next steps, feedback section.

### Quality Checklist

- [ ] Notebooks numbered and individually runnable
- [ ] Metadata filled (level, time, prerequisites)
- [ ] Images in `.webp` on CDN, cover image in `_static/images/guides/`
- [ ] Code follows FiftyOne conventions
- [ ] `index.rst` and `summary.rst` complete
- [ ] `requirements.txt` with exact versions
- [ ] Links and toctrees verified

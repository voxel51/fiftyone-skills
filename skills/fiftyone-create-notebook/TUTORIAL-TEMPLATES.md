# Tutorial Templates

## Contents
- [Canonical Structure](#canonical-structure)
- [Key Differences from Getting Started](#key-differences-from-getting-started)
- [Template: Evaluating Object Detection Models](#template-evaluating-object-detection-models)
- [Template: Clustering Images with Embeddings](#template-clustering-images-with-embeddings)
- [Template: Finding and Fixing Annotation Mistakes](#template-finding-and-fixing-annotation-mistakes)
- [Adaptation Guidelines](#adaptation-guidelines)

---

**Target audience:** Intermediate users who know FiftyOne basics
**Duration:** 20-45 minutes
**Cell count:** 20-35 cells
**Scope:** Deep dive into a specific FiftyOne capability

The templates below are **structural examples** — follow the canonical structure and cell patterns, but adapt the dataset, model, field names, and sections to the user's specific topic. Fetch `https://docs.voxel51.com/llms.txt` for the correct API for any topic.

## Canonical Structure

| Phase | Cells | Content |
|---|---|---|
| Introduction | 0-2 | Title + problem statement (real-world motivation) + learning goals |
| Setup | 3-5 | pip install (may need extra packages) + imports + environment check |
| Data | 6-9 | Load dataset + inspect schema + explore specific aspects + App |
| Concept | 10-12 | Explain the capability being demonstrated (theory, intuition, analogies) |
| Application | 13-20 | Apply step-by-step + show intermediate results + explore in App |
| Analysis | 21-25 | Analyze results + create visualizations + draw insights |
| Variation | 26-28 | Alternative approach or parameter tuning |
| Action | 29-31 | Take action on findings (tag, export, filter, curate) |
| Conclusion | 32-34 | Summary + key takeaways + next steps + links |

## Key Differences from Getting Started

- **Problem-driven:** Start with a real-world problem, not just "how to use X"
- **Deeper explanations:** Include theory and intuition, not just code
- **Multiple approaches:** Show variations and parameter tuning
- **Interpretation:** Explain what results mean, not just how to compute them
- **Action-oriented:** End with actionable next steps based on findings

## Template: Evaluating Object Detection Models

### Cell 0 — markdown
```markdown
# Evaluating Object Detection Models in FiftyOne

How good is your object detection model, really? Aggregate metrics like mAP
tell part of the story, but understanding *where* and *why* your model fails
is what drives real improvements.

In this tutorial, you will go beyond mAP to perform a thorough error analysis
using FiftyOne's evaluation framework, including per-class breakdowns,
confusion matrices, precision-recall curves, and evaluation patches that show
you every true positive, false positive, and false negative.
```

### Cell 1 — markdown
```markdown
## What You Will Learn

- Run COCO-style object detection evaluation
- Interpret mAP, per-class precision, and recall
- Visualize confusion matrices and precision-recall curves
- Use evaluation patches to examine individual TP/FP/FN predictions
- Compare model performance across different IoU thresholds
- Identify systematic failure patterns
```

### Cell 2 — code
```python
!pip install -q fiftyone ultralytics
```

### Cell 3 — markdown
```markdown
## Setup
```

### Cell 4 — code
```python
import fiftyone as fo
import fiftyone.zoo as foz
from fiftyone import ViewField as F
```

### Cell 5 — markdown
```markdown
## Load Dataset and Run Inference

We will use a subset of COCO 2017 validation with ground truth annotations,
then run YOLOv8 to generate predictions we can evaluate.
```

### Cell 6 — code
```python
dataset = foz.load_zoo_dataset(
    "coco-2017",
    split="validation",
    max_samples=500,
    seed=51,
    dataset_name="eval-tutorial",
)

model = foz.load_zoo_model("yolov8m-coco-torch")
dataset.apply_model(model, label_field="predictions")

print(dataset)
```

### Cell 7 — markdown
```markdown
## Explore the Data

Before diving into evaluation metrics, browse the dataset in the App to see
both ground truth annotations and model predictions side by side.
```

### Cell 8 — code
```python
session = fo.launch_app(dataset)
```

### Cell 9 — markdown
```markdown
## Understanding COCO Evaluation

COCO-style evaluation matches predictions to ground truth annotations using
Intersection over Union (IoU). A prediction is a **true positive** if its IoU
with a ground truth box exceeds a threshold (default 0.50) and the class matches.
Unmatched predictions are **false positives**, and unmatched ground truth boxes
are **false negatives**.

**mAP** (mean Average Precision) averages the area under the precision-recall
curve across all classes, giving a single number that summarizes detection quality.
```

### Cell 10 — markdown
```markdown
## Run Evaluation
```

### Cell 11 — code
```python
results = dataset.evaluate_detections(
    "predictions",
    gt_field="ground_truth",
    eval_key="eval",
    method="coco",
    compute_mAP=True,
)

results.print_report(classes=["person", "car", "dog", "cat", "truck", "chair"])
print(f"\nmAP: {results.mAP():.3f}")
print(f"mAR: {results.mAR():.3f}")
```

### Cell 12 — markdown
```markdown
## Confusion Matrix

The confusion matrix shows how classes get confused with each other. Large
off-diagonal values indicate classes the model frequently mixes up.
```

### Cell 13 — code
```python
plot = results.plot_confusion_matrix(
    classes=["person", "car", "dog", "cat", "truck", "bus", "chair"],
)
plot.show()
```

### Cell 14 — markdown
```markdown
## Precision-Recall Curves

Precision-recall curves show the tradeoff between precision (how many
predictions are correct) and recall (how many ground truth objects are found)
at different confidence thresholds.
```

### Cell 15 — code
```python
plot = results.plot_pr_curves(classes=["person", "car", "dog", "cat"])
plot.show()
```

### Cell 16 — markdown
```markdown
## Evaluation Patches: Examining Individual Predictions

Evaluation patches transform your dataset into a view where each row is a
single prediction or ground truth annotation, labeled as TP, FP, or FN.
This is the most powerful tool for understanding model errors.
```

### Cell 17 — code
```python
patches = dataset.to_evaluation_patches("eval")

print("Evaluation patch counts:")
print(patches.count_values("type"))

# Examine false positives — predictions with no matching ground truth
fp_view = patches.match(F("type") == "fp")
session.view = fp_view
```

### Cell 18 — markdown
```markdown
### Examining False Negatives

False negatives are ground truth objects the model failed to detect. These
often reveal small, occluded, or unusual-looking objects that the model
struggles with.
```

### Cell 19 — code
```python
# Examine false negatives — ground truth objects the model missed
fn_view = patches.match(F("type") == "fn")
session.view = fn_view
```

### Cell 20 — markdown
```markdown
## High-Error Samples

Some images have more errors than others. Sorting by false positive count
reveals where the model struggles most.
```

### Cell 21 — code
```python
# Samples with the most false positives
high_fp = dataset.sort_by("eval_fp", reverse=True)
session.view = high_fp[:20]

print("Samples with most false positives:")
for sample in high_fp[:5]:
    print(f"  {sample.filepath}: {sample.eval_fp} FP, {sample.eval_fn} FN")
```

### Cell 22 — markdown
```markdown
## Varying IoU Threshold

IoU threshold affects what counts as a "match." A stricter threshold (0.75)
penalizes poorly localized detections, while a lenient threshold (0.25)
focuses on whether the model found the object at all.
```

### Cell 23 — code
```python
# Strict evaluation at IoU 0.75
results_strict = dataset.evaluate_detections(
    "predictions",
    gt_field="ground_truth",
    eval_key="eval_strict",
    method="coco",
    iou=0.75,
    compute_mAP=True,
)
print(f"mAP @ IoU=0.75: {results_strict.mAP():.3f}")
print(f"mAP @ IoU=0.50: {results.mAP():.3f}")
```

### Cell 24 — markdown
```markdown
## Per-Class Analysis

Looking at per-class performance reveals which object categories the model
handles well and which need improvement.
```

### Cell 25 — code
```python
# Filter to a specific class to analyze its errors
person_fp = patches.match(
    (F("type") == "fp") & (F("predictions.detections.label") == "person")
)
print(f"Person false positives: {len(person_fp)}")
session.view = person_fp
```

### Cell 26 — markdown
```markdown
## Tag Problematic Samples

Tag samples with high error rates for further review or re-annotation.
```

### Cell 27 — code
```python
# Tag samples with more than 5 false positives
high_error = dataset.match(F("eval_fp") > 5)
high_error.tag_samples("needs-review")
print(f"Tagged {len(high_error)} samples for review")
```

### Cell 28 — markdown
```markdown
## Conclusion

In this tutorial, you learned how to:

- **Run COCO evaluation** with `evaluate_detections()` to compute mAP and per-class metrics
- **Visualize** confusion matrices and precision-recall curves
- **Examine individual errors** using evaluation patches (TP/FP/FN)
- **Compare IoU thresholds** to understand localization quality
- **Identify failure patterns** by sorting by error counts and filtering by class
- **Tag** problematic samples for review

**Key Takeaways:**
- mAP alone does not tell the full story — always examine patches
- False positives and false negatives have different causes and solutions
- Per-class analysis reveals which categories need more training data

**Next Steps:**
- [Finding Annotation Mistakes](https://docs.voxel51.com/tutorials/detection_mistakes.html)
- [Evaluation Guide](https://docs.voxel51.com/user_guide/evaluation.html)
- [Model Zoo](https://docs.voxel51.com/model_zoo/index.html)
```

### Cell 29 — code
```python
# Cleanup
fo.delete_dataset("eval-tutorial")
```

---

## Template: Clustering Images with Embeddings

### Cell 0 — markdown
```markdown
# Clustering Images with Embeddings in FiftyOne

When working with large image datasets, understanding the visual structure
of your data is crucial. Are there natural groups? Are some images redundant?
Are there outliers that do not belong?

In this tutorial, you will use image embeddings and dimensionality reduction
to visualize your dataset in 2D, discover clusters, and identify interesting
subsets for further analysis.
```

| Cell | Type | Content |
|---|---|---|
| 0 | markdown | Title + problem statement (shown above) |
| 1 | markdown | What You Will Learn: compute CLIP embeddings, UMAP visualization, explore clusters, find outliers |
| 2 | code | `!pip install -q fiftyone umap-learn` |
| 3 | markdown | `## Setup` + import explanation |
| 4 | code | Imports: `fo`, `foz`, `fob`, `F` |
| 5 | markdown | `## Load the Dataset` + explain quickstart dataset |
| 6 | code | `foz.load_zoo_dataset("quickstart", dataset_name="clustering-tutorial")` + `print(dataset)` |
| 7 | markdown | `## Explore in the FiftyOne App` |
| 8 | code | `session = fo.launch_app(dataset)` |
| 9 | markdown | `## What Are Embeddings?` + explain how embeddings capture visual similarity |
| 10 | markdown | `## Dimensionality Reduction` + explain UMAP/t-SNE, why 2D helps humans |
| 11 | markdown | `## Compute Embeddings and Visualization` + explain CLIP model choice |
| 12 | code | `fob.compute_similarity(...)` + `fob.compute_visualization(...)` + `session.view = dataset.view()` |
| 13 | markdown | `## Explore the Embedding Space` + how to use Embeddings panel, color by labels |
| 14 | code | Examine clusters by coloring, lasso selection |
| 15 | markdown | Interpret cluster patterns: what groupings reveal about the data |
| 16 | code | Select and examine specific cluster subsets |
| 17 | markdown | `## Find Outliers with Uniqueness` + explain uniqueness scoring |
| 18 | code | `fob.compute_uniqueness(...)` + sort by uniqueness descending + `session.view` |
| 19 | markdown | `## Examine Redundant Images` + least unique = most redundant |
| 20 | code | Sort by uniqueness ascending + `session.view` |
| 21 | markdown | `## Alternative: t-SNE Visualization` + compare UMAP vs t-SNE tradeoffs |
| 22 | code | `fob.compute_visualization(dataset, brain_key="clip_tsne", method="tsne")` |
| 23 | markdown | `## Tag Interesting Subsets` |
| 24 | code | Tag outliers or clusters for review |
| 25 | markdown | `## Export for Further Analysis` |
| 26 | code | Export tagged subset |
| 27 | markdown | `## Conclusion` + summary + key takeaways + next steps links |
| 28 | code | Cleanup: `fo.delete_dataset("clustering-tutorial")` |

---

## Template: Finding and Fixing Annotation Mistakes

### Cell 0 — markdown
```markdown
# Finding and Fixing Annotation Mistakes with FiftyOne

Annotation quality directly impacts model performance. Even professional
annotators make mistakes — missing objects, wrong labels, imprecise bounding
boxes. Finding these errors manually in large datasets is impractical.

In this tutorial, you will use FiftyOne's brain methods to automatically
surface likely annotation mistakes, rank them by severity, and take
corrective action.
```

| Cell | Type | Content |
|---|---|---|
| 0 | markdown | Title + problem statement (shown above) |
| 1 | markdown | What You Will Learn: compute mistakenness, hardness, find annotation errors, tag for re-annotation |
| 2 | code | `!pip install -q fiftyone ultralytics` |
| 3 | markdown | `## Setup` + import explanation |
| 4 | code | Imports: `fo`, `foz`, `fob`, `F` |
| 5 | markdown | `## Load Dataset and Run Inference` + explain dataset choice, why inference is needed |
| 6 | code | Load detection dataset + apply model + `print(dataset)` |
| 7 | markdown | `## Explore in the FiftyOne App` |
| 8 | code | `session = fo.launch_app(dataset)` |
| 9 | markdown | `## What Is Mistakenness?` + explain concept: model disagreement reveals annotation errors |
| 10 | markdown | How mistakenness scoring works: comparing confident predictions to annotations |
| 11 | markdown | `## Compute Mistakenness` |
| 12 | code | `fob.compute_mistakenness(...)` + sort by mistakenness + `session.view` |
| 13 | markdown | `## Examine Most Likely Mistakes` |
| 14 | code | View top 20 in App, print mistakenness distribution |
| 15 | markdown | Interpret patterns: missing annotations, wrong labels, imprecise boxes |
| 16 | code | Filter to specific error patterns |
| 17 | markdown | `## Compute Hardness` + explain hardness: model uncertainty = ambiguous examples |
| 18 | code | `fob.compute_hardness(...)` + sort by hardness + `session.view` |
| 19 | markdown | `## Cross-Reference Mistakenness and Hardness` + why both together is powerful |
| 20 | code | Filter samples high in both mistakenness and hardness |
| 21 | markdown | Interpret: these samples are most valuable for review |
| 22 | code | View cross-referenced samples in App |
| 23 | markdown | `## Tag for Re-Annotation` |
| 24 | code | Tag likely mistakes + `print()` count |
| 25 | markdown | `## Export Flagged Samples` |
| 26 | code | Export tagged samples for review |
| 27 | markdown | `## Conclusion` + summary + key takeaways + next steps links |
| 28 | code | Cleanup: `fo.delete_dataset(...)` |

## Adaptation Guidelines

When creating a new tutorial for a topic not listed above:

1. **Start with a real-world problem** — "Why would someone need this?"
2. **Load an appropriate dataset** — Pick one that demonstrates the concept well
3. **Explain concepts before code** — 2-3 markdown cells of intuition before applying
4. **Show intermediate results** — Print counts, show distributions, update the App view
5. **Include a variation section** — Try different parameters or an alternative approach
6. **End with action** — Don't just analyze; do something with the results (tag, export, filter)
7. **Keep it under 35 cells** — Focus depth over breadth
8. **Include interpretation** — "The results show that..." not just "The output is..."

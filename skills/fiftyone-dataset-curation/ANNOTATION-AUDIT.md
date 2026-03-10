# Annotation Audit

Deep-dive annotation quality workflow for FiftyOne datasets. All field references are discovered dynamically — never hardcoded.

---

## Prerequisites Check

Before running any annotation audit step:

```
dataset_summary()
get_field_schema(flat=True)
```

From the schema, identify:
1. **Ground truth field** — typically a Detections, Classifications, Keypoints, or Segmentation field
2. **Predictions field** — must exist for mistakenness computation

If no predictions field exists:
> "Annotation audit requires a predictions field. Use the `fiftyone-dataset-inference` skill to generate predictions, then return here."

Do not proceed with mistakenness if predictions are absent.

---

## 1. Mistakenness Detection

**Operator:** `@voxel51/brain/compute_mistakenness`

### What it does

- **Classification**: Adds a `mistakenness` float field per sample (0 = likely correct, 1 = likely wrong)
- **Detection**: Adds:
  - `mistakenness` — overall sample mistakenness score
  - `mistakenness_loc` — localization error (bbox placement is wrong but class may be right)
  - `possible_spurious` — predictions present but no matching GT (possible extra annotations)
  - `possible_missing` — GT present but high-confidence predictions with no GT match (likely missing annotations)

### Step 1: Discover and run operator

```
list_operators(builtin_only=False)
get_operator_schema(operator_uri="@voxel51/brain/compute_mistakenness")
execute_operator(
    operator_uri="@voxel51/brain/compute_mistakenness",
    params={
        "pred_field": "<predictions_field>",    # from schema discovery
        "label_field": "<ground_truth_field>",  # from schema discovery
        "mistakenness_field": "mistakenness"
    }
)
```

Confirm field names with the user before running. This operation writes new fields and cannot be trivially undone.

### Step 2: Review top offenders

```
set_view(sort_by="mistakenness", reverse=True, limit=50)
```

Direct user to the FiftyOne App (use get_session_info() to get the URL) to review samples side-by-side (predictions vs. ground truth).

### Step 3: Tag for review (after user confirmation)

```
tag_samples(["annotation_review"])
```

Ask the user how many top-mistakenness samples to tag before executing.

---

## 2. Hardness Analysis

**Operator:** `@voxel51/brain/compute_hardness`

**Prerequisite:** Predictions field must include logits (softmax probabilities), not just hard labels.

### What it does

Adds a `hardness` float field per sample:
- High hardness = ambiguous, edge-case samples (model is uncertain)
- Low hardness = easy, clearly-classifiable samples

Hard samples are NOT errors — they are valuable for training (teach the model edge cases).

### Run operator

```
list_operators(builtin_only=False)
get_operator_schema(operator_uri="@voxel51/brain/compute_hardness")
execute_operator(
    operator_uri="@voxel51/brain/compute_hardness",
    params={
        "pred_field": "<predictions_field>",    # from schema discovery
        "hardness_field": "hardness"
    }
)
```

### Review hard samples

```
set_view(sort_by="hardness", reverse=True, limit=50)
```

Use cases:
- Tag hard samples for active learning prioritization: `tag_samples(["hard"])`
- Include hard samples in test set to better measure model performance

---

## 3. IoU Duplicate Object Detection (Detection Datasets Only)

**Operator:** `@voxel51/utils/compute_max_ious`

Use for detecting duplicate or heavily overlapping annotations in the same image.

### What it does

Adds a `max_iou` attribute to each detection in the specified field. High IoU (> 0.75) between two annotations in the same image typically indicates duplicate annotations.

### Run operator

```
list_operators(builtin_only=False)
get_operator_schema(operator_uri="@voxel51/utils/compute_max_ious")
execute_operator(
    operator_uri="@voxel51/utils/compute_max_ious",
    params={"field": "<detections_field>"}   # from schema discovery
)
```

### Filter for overlapping annotations

```
set_view(filters={"<detections_field>.detections.max_iou": {"$gt": 0.75}})
```

Adapt the filter path from the detections field name discovered in schema.

### Review in App

Direct user to the FiftyOne App (use get_session_info() to get the URL) to visually confirm duplicates. Offer to tag affected samples:
```
tag_samples(["duplicate_annotations"])
```

---

## 4. Possible Missing Annotations

After running `compute_mistakenness` on a detection dataset, check for samples with possible missing ground truth annotations:

```
set_view(filters={"possible_missing": {"$gt": 0}})
```

These are samples where the model has high-confidence predictions that have no matching ground truth annotation. This often indicates the annotator missed objects.

### Workflow

1. Filter to samples with `possible_missing > 0`
2. Direct user to the FiftyOne App (use `get_session_info()` to get the URL) to review each sample
3. For confirmed missing annotations: tag for re-annotation:
   ```
   tag_samples(["needs_reannotation"])
   ```
4. Export sample IDs and filepaths for re-annotation pipeline

---

## 5. Possible Spurious Annotations

After running `compute_mistakenness`, check for spurious (extra) annotations:

```
set_view(filters={"possible_spurious": {"$gt": 0}})
```

These are samples where ground truth annotations exist but the model consistently predicts nothing there. This may indicate:
- Incorrect class labels in annotations
- Objects annotated that don't belong to any target class
- Annotation tool errors

### Workflow

1. Filter to samples with `possible_spurious > 0`
2. Direct user to the FiftyOne App (use `get_session_info()` to get the URL) for side-by-side review (predictions panel vs. ground truth panel)
3. Tag after confirmation:
   ```
   tag_samples(["spurious_annotations"])
   ```

---

## 6. Side-by-Side Review Workflow

For all annotation audit results, guide the user through systematic App-based review:

1. **Set the sorted view** (use whichever metric is most relevant):
   ```
   set_view(sort_by="mistakenness", reverse=True, limit=100)
   ```

2. **Enable side-by-side panel** in App:
   - Open the Fields panel → enable both ground truth and predictions fields
   - The App will render both label sets simultaneously

3. **Review sample by sample**:
   - Check label correctness
   - Check bbox placement (localization)
   - Check for missing objects
   - Check for spurious annotations

4. **Tag during review** (confirm count before tagging):
   ```
   tag_samples(["annotation_review"])
   ```

5. **Export reviewed sample IDs** for re-annotation:
   ```python
   # Python SDK guidance
   review_view = dataset.match_tags(["annotation_review"])
   sample_ids = review_view.values("id")
   filepaths  = review_view.values("filepath")
   ```

---

## 7. Annotation Consistency via Embeddings

Use embedding similarity to find visually similar samples with inconsistent annotations.

### Prerequisite
CLIP or DINOv2 similarity index must exist (from Phase 5 of SKILL.md).

### Workflow

1. Pick a sample with suspicious annotation
2. Find visually similar samples:
   ```
   execute_operator(
       operator_uri="@voxel51/brain/sort_by_similarity",
       params={"sample_id": "<suspicious_sample_id>", "k": 10, "brain_key": "<sim_key>"}
   )
   ```
3. Compare annotations across similar images in App
4. Flag inconsistent samples

This approach surfaces:
- Same object class annotated differently across similar images
- Missing annotations on similar scenes

---

## 8. Class-Level Consistency

Use aggregations to identify classes with very few samples that may have inconsistent annotation guidelines:

```
count_values("<label_field>.label")
```
or for detection datasets:
```
count_values("<detections_field>.detections.label")
```

**Flags to report:**
- Classes with < 20 samples — annotation guidelines may not be well-established
- Classes where label names are slightly different spellings of the same concept (e.g., `"car"` vs. `"Car"` vs. `"vehicle"`) — use `distinct` to catch these:
  ```
  distinct("<detections_field>.detections.label")
  ```

### Label standardization

If inconsistent label names are found, recommend consolidation:
```python
# Python SDK guidance
# view.map_labels("<detections_field>", {"car": "road_vehicle", "truck": "road_vehicle"})
# view.save()  # REQUIRED after map_labels — never skip
```

Always confirm the remapping dict with the user before running. Present all unique labels and ask which should be merged.

---

## Audit Summary Table

| Issue type | MCP tool / operator | Tag suggestion |
|-----------|--------------------|-|
| Wrong labels | `compute_mistakenness` → sort mistakenness | `annotation_review` |
| Bad bbox placement | `compute_mistakenness` → sort mistakenness_loc | `localization_error` |
| Missing annotations | `possible_missing > 0` filter | `needs_reannotation` |
| Spurious annotations | `possible_spurious > 0` filter | `spurious_annotations` |
| Duplicate bboxes | `compute_max_ious` → IoU > 0.75 | `duplicate_annotations` |
| Hard/ambiguous samples | `compute_hardness` → sort hardness | `hard` |
| Label inconsistency | `distinct` + `count_values` | manual merge |

---
name: fiftyone-dataset-labels
description: Adds or modifies labels on FiftyOne dataset samples. Use when adding classifications, detections, segmentation masks, keypoints, polylines, heatmaps, regressions, temporal detections, or geolocation labels. Also use when bulk-updating label fields or setting custom attributes on existing labels.
---

# Add Labels to FiftyOne Datasets

## Label Types Quick Reference

| Type | Class | List Class | Key Fields |
|------|-------|------------|------------|
| Classification | `fo.Classification` | `fo.Classifications` | `label`, `confidence`, `logits` |
| Detection | `fo.Detection` | `fo.Detections` | `label`, `bounding_box`, `confidence`, `mask` |
| Polyline | `fo.Polyline` | `fo.Polylines` | `label`, `points`, `closed`, `filled` |
| Keypoint | `fo.Keypoint` | `fo.Keypoints` | `label`, `points`, `confidence` (per-point) |
| Segmentation | `fo.Segmentation` | — | `mask` (numpy) or `mask_path` (file) |
| Heatmap | `fo.Heatmap` | — | `map` (numpy) or `map_path` (file) |
| Regression | `fo.Regression` | — | `value` |
| Temporal Detection | `fo.TemporalDetection` | `fo.TemporalDetections` | `label`, `support` ([first, last] frames) |
| GeoLocation | `fo.GeoLocation` | `fo.GeoLocations` | `point`, `line`, `polygon` |

**Bounding box format:** `[x, y, width, height]` — all values in `[0, 1]` relative to image dimensions.

**Keypoint/polyline points:** list of `(x, y)` tuples in `[0, 1]` relative coordinates.

## Adding Labels to Individual Samples

```python
import fiftyone as fo

sample = fo.Sample(filepath="/path/to/image.jpg")

# Classification
sample["prediction"] = fo.Classification(label="cat", confidence=0.95)

# Multi-label classification
sample["tags"] = fo.Classifications(
    classifications=[
        fo.Classification(label="outdoor", confidence=0.9),
        fo.Classification(label="daytime", confidence=0.8),
    ]
)

# Object detections
sample["objects"] = fo.Detections(
    detections=[
        fo.Detection(
            label="dog",
            bounding_box=[0.1, 0.2, 0.5, 0.6],
            confidence=0.92,
        ),
    ]
)

# Segmentation (numpy array of integer class IDs matching image dimensions)
import numpy as np
mask = np.zeros((height, width), dtype=np.uint8)
mask[100:300, 50:200] = 1
sample["segmentation"] = fo.Segmentation(mask=mask)

# Segmentation from file
sample["segmentation"] = fo.Segmentation(mask_path="/path/to/mask.png")

# Keypoints
sample["pose"] = fo.Keypoints(
    keypoints=[
        fo.Keypoint(
            label="person",
            points=[(0.4, 0.2), (0.45, 0.3), (0.35, 0.3)],
            confidence=[0.9, 0.85, 0.87],
        )
    ]
)

# Polylines
sample["boundaries"] = fo.Polylines(
    polylines=[
        fo.Polyline(
            label="fence",
            points=[[(0.1, 0.1), (0.9, 0.1), (0.9, 0.9)]],
            closed=False,
            filled=False,
        )
    ]
)

# Heatmap (numpy array or file path)
sample["heatmap"] = fo.Heatmap(map=heatmap_array)
sample["heatmap"] = fo.Heatmap(map_path="/path/to/heatmap.png")

# Regression
sample["quality"] = fo.Regression(value=0.85)

# Temporal detection (video samples)
sample["actions"] = fo.TemporalDetections(
    detections=[
        fo.TemporalDetection(label="running", support=[10, 120], confidence=0.91)
    ]
)

# GeoLocation
sample["location"] = fo.GeoLocation(
    point=[-73.9855, 40.7580],
    polygon=[[
        [-73.949, 40.834], [-73.896, 40.815],
        [-73.998, 40.696], [-73.949, 40.834],
    ]],
)
```

## Custom Attributes on Labels

Any label supports arbitrary custom attributes:

```python
# Inline as keyword arguments
detection = fo.Detection(
    label="car",
    bounding_box=[0.1, 0.2, 0.3, 0.4],
    color="red",
    occluded=True,
)

# Using typed attributes
detection = fo.Detection(
    label="car",
    bounding_box=[0.1, 0.2, 0.3, 0.4],
    attributes={
        "make": fo.CategoricalAttribute(value="Toyota"),
        "year": fo.NumericAttribute(value=2020),
    },
)
```

## Bulk Operations (Preferred for Large Datasets)

### `set_values` — set a field across all samples

```python
import fiftyone as fo

dataset = fo.load_dataset("my-dataset")

# List syntax: one value per sample, in order
labels = [fo.Classification(label=lbl) for lbl in predicted_labels]
dataset.set_values("predictions", labels)

# Dict syntax (recommended): map sample IDs to values
values = {sid: fo.Classification(label=lbl) for sid, lbl in zip(sample_ids, predicted_labels)}
dataset.set_values("predictions", values, key_field="id")
```

### `set_label_values` — modify attributes on existing labels

```python
from fiftyone import ViewField as F

# Tag low-confidence detections
view = dataset.filter_labels("predictions", F("confidence") < 0.1)

# List syntax: provide sample_id, label_id, and value
values = []
for sid, lids in zip(*view.values(["id", "predictions.detections.id"])):
    for lid in lids:
        values.append({"sample_id": sid, "label_id": lid, "value": True})

dataset.set_label_values("predictions.detections.is_low_conf", values)
```

### `iter_samples(autosave=True)` — loop with auto-save

```python
for sample in dataset.iter_samples(autosave=True, progress=True):
    sample["score"] = fo.Regression(value=compute_score(sample))
```

## Common Patterns

### Add model predictions alongside ground truth

```python
dataset = fo.load_dataset("my-dataset")

# Use a different field name to avoid overwriting ground truth
predictions = [fo.Detections(detections=dets) for dets in model_outputs]
dataset.set_values("predictions", predictions)
```

### Add labels from external annotation files

```python
import json

dataset = fo.load_dataset("my-dataset")

with open("annotations.json") as f:
    annotations = json.load(f)

values = {}
for ann in annotations:
    values[ann["sample_id"]] = fo.Detections(
        detections=[
            fo.Detection(
                label=det["label"],
                bounding_box=det["bbox"],
                confidence=det.get("confidence"),
            )
            for det in ann["detections"]
        ]
    )

dataset.set_values("ground_truth", values, key_field="id")
```

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Bounding box in pixel coordinates | Use relative `[0, 1]` values: divide by image width/height |
| Using `sample.save()` in a loop | Use `iter_samples(autosave=True)` or `set_values()` |
| Overwriting ground truth | Use a different field name (e.g., `predictions`) |
| Segmentation mask wrong size | Mask must match image dimensions exactly |
| Forgetting to call `dataset.save()` after `set_values` | `set_values` saves automatically — no extra call needed |

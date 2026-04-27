# Model Predicition Label Return Types

### Image Operations

**Image models must return a single `fo.Label` instance per sample — NOT a dict.**

| Operation | Return Type | Example |
|-----------|-------------|---------|
| VQA / Caption / OCR | `fo.Classification` | `fo.Classification(label="A dog on a beach")` |
| Single classification | `fo.Classification` | `fo.Classification(label="cat")` |
| Multi-label classification | `fo.Classifications` | `fo.Classifications(classifications=[fo.Classification(label="outdoor"), ...])` |
| Tagging | `fo.Classifications` | Same as multi-label classification |
| Object detection | `fo.Detections` | `fo.Detections(detections=[fo.Detection(label="car", bounding_box=[x,y,w,h]), ...])` |
| Keypoint detection | `fo.Keypoints` | `fo.Keypoints(keypoints=[fo.Keypoint(label="face", points=[[x,y]]), ...])` |
| Instance segmentation | `fo.Detections` | `fo.Detections(detections=[fo.Detection(label="cat", mask=mask_array), ...])` |
| Semantic segmentation | `fo.Segmentation` | `fo.Segmentation(mask=mask_array)` |

**Key details:**
- Bounding boxes use `[x, y, width, height]` in `[0, 1]` normalized coordinates
- Keypoints use `[[x, y], ...]` in `[0, 1]` normalized coordinates
- Text responses (VQA, caption, OCR) are wrapped in `fo.Classification(label=text)` — do NOT return raw strings

### Video Operations (frame-level)

Video models may return a **dict** from `predict_all()`, but ONLY when the dict uses **integer frame numbers** as keys. FiftyOne's `add_labels` detects this and merges into `sample.frames`.

```python
# Sample-level labels (simple string/label) — return single Label or dict with string keys
{"summary": "A person walks across a park"}

# Frame-level labels — dict with integer keys
{
    1: {"objects": fo.Detections(detections=[...])},
    15: {"objects": fo.Detections(detections=[...])},
}

# Mixed sample + frame-level — dict with both string and integer keys
{
    "summary": "A person walks across a park",
    1: {"objects": fo.Detections(detections=[...])},
}
```

Video-specific label types:
- `fo.TemporalDetection` / `fo.TemporalDetections` — time-range events on the full video
- Frame-level `fo.Detections` — per-frame bounding boxes (stored in `sample.frames[N]`)

## Storing Metadata as Dynamic Attributes

Do NOT create wrapper dicts to store extra data alongside labels. Instead, use **dynamic attributes** on the Label instance itself:

```python
# WRONG — returns a dict, breaks nested label_field
def _parse_output(self, text, reasoning):
    return {"detections": fo.Detections(...), "raw": text, "reasoning": reasoning}

# CORRECT — returns single Label, metadata as dynamic attributes
def _parse_output(self, text, reasoning):
    dets = fo.Detections(detections=[...])
    if reasoning:
        for det in dets.detections:
            det["reasoning"] = reasoning
    return dets
```

Dynamic attributes can be set on any Label subclass:
```python
label = fo.Classification(label="cat")
label["confidence_raw"] = 0.95
label["reasoning"] = "The image shows pointed ears and whiskers..."
label["model_name"] = "gemma-4-E4B-it"
```

Users access them via:
```python
sample.predictions["reasoning"]       # on Classification
sample.predictions.detections[0]["reasoning"]  # on individual Detection
```

## How FiftyOne's add_labels Works

Understanding the dispatch logic in `Sample.add_labels()`:

```python
labels = model.predict(img)

if isinstance(labels, dict):
    if all keys are integers:
        → Frame-level labels: merge into sample.frames
    elif any key is an integer:
        → Mixed: string keys become sample fields, int keys become frame fields
    else:
        → Multiple sample fields: each key maps to label_field + "_" + key
elif labels is a Label instance:
    → Single field: stored directly in label_field
```

The `label_field` key mapping for dicts:
```python
# When label_field is a string (e.g., "predictions"):
key_fn = lambda k: "predictions_" + k
# {"detections": ..., "raw": ...} → sample.predictions_detections, sample.predictions_raw

# When label_field is a dict:
key_fn = lambda k: label_field.get(k, k)
# label_field={"detections": "preds"} → sample.preds

# When label_field is None:
key_fn = lambda k: k
# {"detections": ...} → sample.detections
```

## Coordinate Normalization

FiftyOne uses `[0, 1]` normalized coordinates for all spatial labels:

- **Bounding boxes**: `[x, y, width, height]` where `(x, y)` is top-left corner
- **Keypoints**: `[[x, y], ...]`
- **Polylines**: `[[[x, y], ...], ...]`

If a model outputs coordinates in pixel space or 0-1000 scale, normalize before creating labels:
```python
# From 0-1000 scale (common in VLMs like Gemma4, Qwen3.5)
x1, y1, x2, y2 = raw_bbox
fo.Detection(
    label=label,
    bounding_box=[x1/1000, y1/1000, (x2-x1)/1000, (y2-y1)/1000],
)

# From pixel coordinates
fo.Detection(
    label=label,
    bounding_box=[x/img_w, y/img_h, w/img_w, h/img_h],
)
```

## Quick Checklist

When implementing `predict()` / `predict_all()` for a FiftyOne zoo model:

- [ ] Image operations return a single `fo.Label` subclass, not a dict
- [ ] Text outputs (VQA, caption, OCR) wrapped in `fo.Classification(label=text)`
- [ ] Detection boxes are `[x, y, w, h]` in `[0, 1]` range
- [ ] Keypoints are `[[x, y], ...]` in `[0, 1]` range
- [ ] Extra metadata stored as dynamic attributes on the Label, not in wrapper dicts
- [ ] Video frame-level results use integer keys in the return dict
- [ ] `collate_fn` inherited from `TorchModelMixin` (not overridden) — see `/fiftyone-zoo-remote-model` skill for details
- [ ] `build_get_item` returns `ImageGetItem(raw_inputs=True)` — no custom `GetItem` subclass in zoo module

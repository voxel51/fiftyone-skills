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
- Bounding boxes: `[x, y, width, height]` in `[0, 1]`; keypoints: `[[x, y], ...]` in `[0, 1]`
- Text responses (VQA, caption, OCR) wrapped in `fo.Classification(label=text)` — do NOT return raw strings

### Video Operations (frame-level)

Video models may return a **dict** from `predict_all()`, but ONLY when the dict uses **integer frame numbers** as keys. FiftyOne's `add_labels` detects this and merges into `sample.frames`.

```python
# Frame-level — dict with integer keys
{1: {"objects": fo.Detections(...)}, 15: {"objects": fo.Detections(...)}}

# Mixed sample + frame-level — string and integer keys
{"summary": "A person walks", 1: {"objects": fo.Detections(...)}}
```

Video-specific types: `fo.TemporalDetection` / `fo.TemporalDetections` (time-range events); frame-level `fo.Detections` (stored in `sample.frames[N]`).

## Storing Metadata as Dynamic Attributes

Do NOT wrap labels in a dict. Use **dynamic attributes** on the Label itself:

```python
# WRONG — dict return triggers silent field-splitting (see below)
def _parse_output(self, text, reasoning):
    return {"label": "cat", "reasoning": reasoning}

# CORRECT — single Label with dynamic attribute
def _parse_output(self, text, reasoning):
    cls = fo.Classification(label="cat")
    cls["reasoning"] = reasoning
    return cls
```

### The silent `predictions_<key>` failure

If the model returns `{"label": "cat", "reasoning": "..."}` and the user calls `dataset.apply_model(model, label_field="predictions")`, FiftyOne does NOT raise. It silently splits the dict into top-level fields:

```
sample.predictions_label       # fo.Classification(label="cat")
sample.predictions_reasoning   # "..." (string field)
```

There is no `sample.predictions` field. Downstream `sample.predictions.label` fails with `AttributeError` — `predictions` is a Classification at `predictions_label`, not at `predictions`. Grep signature: `predictions_<key>`. Fix: return a single Label with `label["reasoning"] = ...`.

Users access dynamic attributes via `sample.predictions["reasoning"]` or `sample.predictions.detections[0]["reasoning"]`.

## `add_labels` Dispatch (reference)

`Sample.add_labels()` branches on the return value:

| Return | Stored as |
|--------|-----------|
| `Label` instance | Single field at `label_field` |
| Dict, all integer keys | Frame-level, merged into `sample.frames` |
| Dict, mixed int + string keys | String → sample fields, int → frame fields |
| Dict, all string keys | Each key → `label_field + "_" + key` (the silent-split failure above) |

## Coordinate Normalization

FiftyOne uses `[0, 1]` normalized coordinates for all spatial labels:

- **Bounding boxes**: `[x, y, width, height]` where `(x, y)` is top-left corner
- **Keypoints**: `[[x, y], ...]`
- **Polylines**: `[[[x, y], ...], ...]`

If a model outputs pixel space or 0-1000 scale, normalize before creating labels:
```python
# From pixel coordinates
fo.Detection(label=label, bounding_box=[x/img_w, y/img_h, w/img_w, h/img_h])
```

For VLM-specific quirks (PaLI `[y, x, h, w]` order, 0–1000 scales), see `VLM-PATTERNS.md`.

## Quick Checklist

- [ ] Image ops return a single `fo.Label` subclass, not a dict
- [ ] Text outputs wrapped in `fo.Classification(label=text)`
- [ ] Detection boxes `[x, y, w, h]` in `[0, 1]`; keypoints `[[x, y], ...]` in `[0, 1]`
- [ ] Extra metadata as dynamic attributes on the Label, not wrapper dicts
- [ ] Video frame-level results use integer keys
- [ ] `collate_fn` inherited from `TorchModelMixin`; `build_get_item` returns `ImageGetItem(raw_inputs=True)`

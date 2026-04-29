# zoo.py — Class Hierarchy

## Use these, don't replace these

**Framework-first**: FiftyOne already provides the pickle-safe primitives. Subclassing or overriding these re-introduces the **Worker-pickle constraint** failures (see DATALOADER.md).

| Concern | Use this | Do NOT |
|---------|----------|--------|
| Batch collation | `TorchModelMixin.collate_fn` (inherited) | Override `collate_fn` |
| Dataset item loading | `fiftyone.utils.torch.ImageGetItem(raw_inputs=True)` | Subclass `GetItem` |
| `transforms` / `preprocess` / `ragged_batches` / `needs_fields` / `has_collate_fn` | Implement on your model class | These are the seams — implement, don't avoid |

## Config

```python
import fiftyone.utils.torch as fout

class MyModelConfig(fout.TorchImageModelConfig):
    def __init__(self, d: dict):
        if "raw_inputs" not in d:
            d["raw_inputs"] = True
        super().__init__(d)
        self.model_path = self.parse_string(d, "model_path", default="org/model")
```

## Model — multi-inheritance order matters

```python
import fiftyone.core.models as fom
from fiftyone.core.models import SupportsGetItem, TorchModelMixin
from fiftyone.utils.torch import ImageGetItem

class MyBaseModel(fom.Model, fom.SamplesMixin, SupportsGetItem, TorchModelMixin):
    def __init__(self, config):
        fom.SamplesMixin.__init__(self)
        SupportsGetItem.__init__(self)
        self._preprocess = False
        self.config = config

    @property
    def transforms(self): return None

    @property
    def preprocess(self) -> bool: return self._preprocess
    @preprocess.setter
    def preprocess(self, value: bool): self._preprocess = value

    @property
    def ragged_batches(self) -> bool: return False

    @property
    def needs_fields(self) -> dict: return self._fields
    @needs_fields.setter
    def needs_fields(self, fields: dict): self._fields = fields

    @property
    def has_collate_fn(self) -> bool: return True

    def build_get_item(self, field_mapping=None) -> ImageGetItem:
        return ImageGetItem(field_mapping=field_mapping, raw_inputs=True)
```

## predict / predict_all — three input types

FiftyOne calls `predict` from three different code paths. **All three must be handled** or the model breaks on one invocation shape:

| Source | Type | Where from |
|--------|------|-----------|
| DataLoader (multi-worker) | `PIL.Image` | `ImageGetItem(raw_inputs=True)` |
| Single-sample path | `str` (filepath) | `_apply_image_model_single` |
| Direct API | `dict` | User code calling `model.predict({...})` |

Dispatch on `isinstance`:

```python
def predict(self, arg, sample=None):
    return self.predict_all([arg], samples=[sample] if sample else None)[0]

def predict_all(self, batch, samples=None):
    results = []
    for i, item in enumerate(batch):
        sample = samples[i] if samples and i < len(samples) else None
        if isinstance(item, dict):
            image = item.get("filepath", item.get("image"))
            prompt = item.get("prompt")
        elif isinstance(item, str):
            image, prompt = item, None     # filepath
        else:
            image, prompt = item, None     # PIL Image

        if prompt is None and sample and "prompt_field" in self._fields:
            fn = self._fields["prompt_field"]
            if sample.has_field(fn):
                prompt = sample.get_field(fn)
        prompt = prompt or self.config.prompt
        results.append(self._run_inference(image, prompt))
    return results
```

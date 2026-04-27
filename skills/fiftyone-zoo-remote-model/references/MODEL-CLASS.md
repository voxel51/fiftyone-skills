# zoo.py — Class Hierarchy

## Config

```python
import fiftyone.utils.torch as fout

class MyModelConfig(fout.TorchImageModelConfig):
    def __init__(self, d: dict):
        if "raw_inputs" not in d:
            d["raw_inputs"] = True   # Feed raw images, not stacked tensors
        super().__init__(d)
        self.model_path = self.parse_string(d, "model_path", default="org/model")
        # ... other config params
```

## Model

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
        # ... model state

    # -- Required properties --
    @property
    def transforms(self):
        return None

    @property
    def preprocess(self) -> bool:
        return self._preprocess

    @preprocess.setter
    def preprocess(self, value: bool):
        self._preprocess = value

    @property
    def ragged_batches(self) -> bool:
        return False

    @property
    def needs_fields(self) -> dict:
        return self._fields

    @needs_fields.setter
    def needs_fields(self, fields: dict):
        self._fields = fields

    @property
    def has_collate_fn(self) -> bool:
        return True
    # See DATALOADER.md for collate_fn and GetItem options (built-in vs custom)

    def build_get_item(self, field_mapping=None) -> ImageGetItem:
        return ImageGetItem(field_mapping=field_mapping, raw_inputs=True)
```

## predict / predict_all — Handle Multiple Input Types

With `ImageGetItem(raw_inputs=True)`, the DataLoader delivers PIL Images. But FiftyOne's single-sample path (`_apply_image_model_single`) passes filepath strings. Direct API calls may pass dicts. Handle all three:

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
            image = item       # filepath from simple path
            prompt = None
        else:
            image = item       # PIL Image from DataLoader
            prompt = None

        # Get prompt from sample fields if needed
        if prompt is None and sample and "prompt_field" in self._fields:
            fn = self._fields["prompt_field"]
            if sample.has_field(fn):
                prompt = sample.get_field(fn)

        prompt = prompt or self.config.prompt
        results.append(self._run_inference(image, prompt))
    return results
```

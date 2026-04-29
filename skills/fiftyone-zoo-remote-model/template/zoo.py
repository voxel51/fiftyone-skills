# worker-pickle constraint: no pickle-bound objects defined in this module
from __future__ import annotations

from typing import Any

import fiftyone.core.models as fom
import fiftyone.utils.torch as fout
from fiftyone.core.models import SupportsGetItem, TorchModelMixin
from fiftyone.utils.torch import ImageGetItem


class YourModelConfig(fout.TorchImageModelConfig):
    def __init__(self, d: dict):
        if "raw_inputs" not in d:
            d["raw_inputs"] = True
        super().__init__(d)
        self.model_path = self.parse_string(d, "model_path", default="org/your-model")
        self.model_name = d.get("model_name")


# framework-first: do not subclass GetItem (use ImageGetItem)
# framework-first: do not override collate_fn (inherited from TorchModelMixin)
class YourModel(fom.Model, fom.SamplesMixin, SupportsGetItem, TorchModelMixin):
    def __init__(self, config: YourModelConfig):
        fom.SamplesMixin.__init__(self)
        SupportsGetItem.__init__(self)
        self.config = config
        self._preprocess = False
        self._fields: dict = {}
        self._model = self._load_model(config)

    def _load_model(self, config: YourModelConfig) -> Any:
        raise NotImplementedError("Load and return the underlying model here.")

    @property
    def transforms(self) -> Any | None:
        return None

    @property
    def preprocess(self) -> bool:
        return self._preprocess

    @preprocess.setter
    def preprocess(self, value: bool) -> None:
        self._preprocess = value

    @property
    def ragged_batches(self) -> bool:
        return False

    @property
    def needs_fields(self) -> dict:
        return self._fields

    @needs_fields.setter
    def needs_fields(self, fields: dict) -> None:
        self._fields = fields

    @property
    def has_collate_fn(self) -> bool:
        return True

    def build_get_item(self, field_mapping: dict | None = None) -> ImageGetItem:
        return ImageGetItem(field_mapping=field_mapping, raw_inputs=True)

    def predict(self, arg: Any, sample: Any | None = None) -> Any:
        return self.predict_all([arg], samples=[sample] if sample else None)[0]

    def predict_all(self, args: list, samples: list | None = None) -> list:
        # schema compliance ≠ correctness: verify outputs against ground-truth examples
        for item in args:
            if isinstance(item, dict):
                pass  # {"filepath"|"image": ..., "prompt": ...}
            elif isinstance(item, str):
                pass  # filepath
            else:
                pass  # PIL.Image
        raise NotImplementedError("Run inference and return list[fo.Label].")

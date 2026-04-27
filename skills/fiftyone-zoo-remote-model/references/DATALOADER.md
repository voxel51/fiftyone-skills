# DataLoader Multi-Worker Pickle Compatibility

FiftyOne's `dataset.apply_model()` uses a PyTorch DataLoader with `num_workers > 0` for models that inherit `SupportsGetItem` or `TorchModelMixin`. Two objects are pickled for workers: the `collate_fn` and the `GetItem` from `build_get_item()`.

## macOS Pickle Restriction

On macOS, DataLoader workers use `spawn` by default. FiftyOne loads remote zoo sources via `importlib.util.spec_from_file_location`, registering the module in the parent's `sys.modules` only. Spawned workers on macOS CANNOT import the zoo source module, so **custom classes defined in `zoo.py` will cause `ModuleNotFoundError` when pickled for workers on macOS.**

On Linux and Windows, `fork`-based workers inherit the parent's `sys.modules`, so custom `collate_fn` and `GetItem` subclasses defined in `zoo.py` work normally with `num_workers > 0`.

## Platform-Aware num_workers

To support custom picklable objects cross-platform, gate `num_workers` on the platform:

```python
import sys

num_workers = user_provided_num_workers  # or the default
dataset.apply_model(
    model,
    label_field="predictions",
    num_workers=num_workers if sys.platform != "darwin" else 0,
)
```

Setting `num_workers=0` on macOS runs inference in the main process, avoiding the pickle issue entirely while still allowing custom `GetItem` and `collate_fn` on other platforms.

## Option A: Use FiftyOne Built-ins (works everywhere)

If you don't need custom picklable objects, use FiftyOne's own classes. This approach works on all platforms with any `num_workers` value.

### collate_fn — Inherit, Don't Override

`TorchModelMixin` provides `collate_fn` as a `@staticmethod` that returns `batch` as-is. It's defined in `fiftyone.core.models` — always importable by workers.

```python
# Inherit from TorchModelMixin — works on all platforms
@property
def has_collate_fn(self) -> bool:
    return True
# collate_fn is inherited — do NOT define it
```

### GetItem — Use FiftyOne's ImageGetItem

`fiftyone.utils.torch.ImageGetItem` is a concrete `GetItem` subclass that loads images from filepaths. With `raw_inputs=True`, it returns PIL Images directly. Workers can always import it.

```python
# Uses fiftyone's class — works on all platforms
def build_get_item(self, field_mapping=None) -> ImageGetItem:
    return ImageGetItem(field_mapping=field_mapping, raw_inputs=True)
```

## Option B: Custom Classes (requires platform-aware num_workers)

Custom `collate_fn` and `GetItem` subclasses defined in `zoo.py` are viable when paired with the platform-aware `num_workers` pattern above. On macOS, `num_workers=0` avoids pickling entirely; on other platforms, workers can import the module normally.

```python
# Custom collate_fn — works on Linux/Windows with workers, macOS with num_workers=0
def _my_collate(batch):
    # custom batching logic
    return batch

@property
def collate_fn(self):
    return _my_collate

# Custom GetItem — works on Linux/Windows with workers, macOS with num_workers=0
class MyGetItem(GetItem):
    def __call__(self, d):
        return {"filepath": d["filepath"]}

def build_get_item(self, field_mapping=None):
    return MyGetItem(field_mapping=field_mapping)
```

**Important:** If using custom classes, you MUST use the platform-aware `num_workers` pattern in your `apply_model()` call, or macOS users will hit `ModuleNotFoundError`.

## How FiftyOne Dispatches apply_model

```
apply_model(model, ...)
│
├─ isinstance(model, (SupportsGetItem, TorchModelMixin))?
│  YES → _apply_image_model_data_loader()   ← multi-worker DataLoader path
│  │     Creates DataLoader with num_workers, pickles GetItem + collate_fn
│  │     Calls model.predict_all(batch, samples=sample_batch)
│  │
│  NO, batch_size provided?
│     YES → _apply_image_model_batch()      ← batch path, no DataLoader
│     │     Calls model.predict_all([filepaths], samples=batch)
│     │
│     NO → _apply_image_model_single()       ← simple path
│          Calls model.predict(filepath, sample=sample) per sample
```

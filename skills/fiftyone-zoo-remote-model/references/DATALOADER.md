# DataLoader Multi-Worker Pickle Compatibility

`dataset.apply_model()` runs a PyTorch DataLoader for any model inheriting `SupportsGetItem` or `TorchModelMixin`. The `collate_fn` and the `GetItem` instance are pickled across the worker boundary. If either resolves to a module the worker cannot import, you get `ModuleNotFoundError` from the spawned worker.

## 1. Why workers can't import your module

FiftyOne loads remote zoo sources via `importlib.util.spec_from_file_location`. The module is registered in the **parent's** `sys.modules`, but its directory is **never** added to `sys.path`.

| Platform | Worker start | Result |
|---|---|---|
| macOS | `spawn` (default) | Fresh interpreter; no inherited `sys.modules`; cannot import zoo source. |
| Linux, Python 3.14+ POSIX | `spawn`/`forkserver` | Same as macOS. |
| Linux (current default) | `fork` | Inherits parent `sys.modules`; **silently masks the bug**. |

A zoo source that "works on Linux" can fail on macOS or after a Python version bump. Concrete signature:

```
ModuleNotFoundError: No module named 'fiftyone.zoo.models.<your-source>'
```

## 2. The pickle-resolution rule

Pickle serializes objects by **qualified module path**, not by value. If a `collate_fn`, `GetItem`, or any closure is defined in your `zoo.py`, pickle stores `your_zoo_source.SomeClass`. The worker `import`s that path, fails, and dies before your code runs.

Principle: **Worker-pickle constraint** — anything crossing the worker boundary must resolve to a module the worker can import.

## 3. The right answer

Use what the framework already provides. Both pickle to modules workers can always import.

| Need | Use | Pickles to |
|---|---|---|
| Collate | `TorchModelMixin.collate_fn` (inherit, don't override) | `fiftyone.core.models` |
| Per-sample loading | `fiftyone.utils.torch.ImageGetItem(raw_inputs=True)` | `fiftyone.utils.torch` |

```python
from fiftyone.utils.torch import ImageGetItem

@property
def has_collate_fn(self) -> bool:
    return True   # framework-first: inherit collate_fn from TorchModelMixin

def build_get_item(self, field_mapping=None) -> ImageGetItem:
    return ImageGetItem(field_mapping=field_mapping, raw_inputs=True)
```

Principle: **Framework-first** — use FiftyOne's existing classes before defining your own.

## 4. Why `num_workers=0` is not the fix

It removes worker pickling entirely. Multi-worker is **non-negotiable**: production-scale datasets require it for I/O parallelism. A zoo source that requires `num_workers=0` is broken, not "tradeoff-configured." Validate with default `num_workers` on macOS before shipping.

## 5. Why reference implementations may be wrong

Several widely-copied remote zoo sources define nested-closure collate functions or custom `GetItem` subclasses inline in `zoo.py`. They run on Linux fork-workers and silently break on macOS spawn-workers. Copying them propagates the bug.

Verification: run `dataset.apply_model(model)` with **default** `num_workers` on macOS before treating any reference as a template.

Principle: **Reference implementations need verification.**

## 6. Wrong fixes that look right

Preserved so the next agent does not re-walk the journey.

- **Module-level helper with `__module__` reassigned to your zoo source** — workers still cannot import your zoo source.
- **Nested closure inside a property** — closures are unpicklable; raises `PicklingError` immediately.
- **Custom `__reduce__` returning a string-encoded `lambda`** — fragile, opaque, and breaks again on the next pickle protocol.
- **`PYTHONPATH` injection from `__init__.py`** — mutates global interpreter state on import; affects unrelated code; still racy with already-spawned workers.

The only correct fix is Section 3.

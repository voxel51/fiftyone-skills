# Manifest & Entry Point

## manifest.json

**Must have a top-level `name` field.** FiftyOne skips manifests without it. The `name` determines the subdirectory under `model_zoo_dir` and the Python module name.

> **First check on silent failure.** If `register_zoo_model_source` "succeeds" but `load_zoo_model` cannot find the model, verify the top-level `name` is present. Missing-`name` is a silent skip — frequently replicated bug.

```json
{
    "name": "my-org/my-model",
    "url": "https://github.com/my-org/my-model",
    "models": [
        {
            "base_name": "org/model-variant",
            "base_filename": "model-variant",
            "author": "Author Name",
            "description": "Brief model description.",
            "requirements": {
                "packages": ["torch", "transformers>=4.50"],
                "cpu": {"support": true},
                "gpu": {"support": true}
            },
            "tags": ["detection", "classification", "torch", "VLM"]
        }
    ]
}
```

## __init__.py

Exports functions called by FiftyOne's zoo machinery. Uses relative imports for `zoo.py`.

```python
from .zoo import MyImageModel, MyImageModelConfig, MyVideoModel, MyVideoModelConfig

def download_model(model_name: str, model_path: str) -> None:
    """Download model weights to model_path. MUST be idempotent — safe to
    call when weights already exist at model_path (no-op or re-verify)."""
    ...

def load_model(model_name: str | None = None, model_path: str | None = None, **kwargs) -> MyImageModel | MyVideoModel:
    """Load and return a fom.Model instance. kwargs passed from load_zoo_model."""
    config = MyImageModelConfig({**kwargs})
    return MyImageModel(config)

def resolve_input(model_name: str, ctx) -> types.Property | None:
    """Define operator UI inputs for FiftyOne App (optional)."""
    ...
```

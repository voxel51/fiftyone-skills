"""Entry points for the remote zoo source. Manifest top-level `name` is required."""

from typing import Any

# framework-first: relative import keeps the worker-pickle path resolvable
from .zoo import YourModel, YourModelConfig


def download_model(model_name: str, model_path: str) -> None:
    """Download weights to model_path. FiftyOne guards re-calls; not always invoked."""
    raise NotImplementedError


def load_model(
    model_name: str | None = None,
    model_path: str | None = None,
    **kwargs: Any,
) -> YourModel:
    """FiftyOne calls with positional model_name, model_path, and forwarded kwargs."""
    config_dict: dict[str, Any] = {"model_path": model_path, "model_name": model_name}
    config_dict.update(kwargs)
    return YourModel(YourModelConfig(config_dict))


# Optional: implement only if invoked from an operator UI.
# def resolve_input(model_name: str, ctx) -> "fiftyone.operators.types.Property | None":
#     return None

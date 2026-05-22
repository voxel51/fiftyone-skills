# Zoo Remote Model

Build FiftyOne remote model zoo integrations that work with `register_zoo_model_source`, multi-worker DataLoader, and `dataset.apply_model`.

## Install

```bash
curl -sL skil.sh | sh -s -- voxel51/fiftyone-skills
```

When prompted, select **fiftyone-zoo-remote-model** from the menu.

## Requirements

- [FiftyOne](https://docs.voxel51.com/getting_started/install.html)
- Python 3.9+
- PyTorch (or the framework your model uses)

## Usage

Ask your AI assistant:

```
"Build a remote zoo model wrapper for my Hugging Face detection model"
"Create a FiftyOne zoo source with manifest.json for my custom classifier"
"My zoo model raises ModuleNotFoundError from DataLoader workers — fix it"
"Add VLM-style prompt dispatch to my zoo model"
```

The skill scaffolds the source layout (`manifest.json`, `__init__.py`, `zoo.py`), wires the model class against `TorchModelMixin` + `SupportsGetItem`, and walks the validation steps so the result works under multi-worker DataLoader and `dataset.apply_model`.

## Example

Register and apply a zoo source written with this skill:

```python
import fiftyone as fo
import fiftyone.zoo as foz

foz.register_zoo_model_source("/path/to/your-zoo-source")
model = foz.load_zoo_model("your-model-name")

dataset = fo.load_dataset("your-dataset")
dataset.apply_model(model, label_field="predictions")
```

## See also

- [Remotely-sourced zoo models](https://docs.voxel51.com/model_zoo/remote.html)
- [FiftyOne model zoo source](https://github.com/voxel51/fiftyone/tree/develop/fiftyone/zoo/models)

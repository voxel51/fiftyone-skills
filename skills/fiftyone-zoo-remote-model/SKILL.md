---
name: fiftyone-zoo-remote-model
description: Build FiftyOne remote model zoo integrations that work with register_zoo_model_source, multi-worker DataLoader, and dataset.apply_model. Covers file structure, manifest, class hierarchy, DataLoader pickle compatibility, label return types, and common pitfalls.
allowed-tools: Read, Grep, Glob, Agent, WebFetch, Write, Edit
---

# FiftyOne Remote Model Zoo — Integration Guide

Use this skill when building a new FiftyOne model zoo integration intended for remote registration via `foz.register_zoo_model_source()`, or when debugging issues with an existing one.

Reference documentation:
- FiftyOne remote model zoo docs: https://docs.voxel51.com/model_zoo/remote.html
- [MANIFEST.md](references/MANIFEST.md) — manifest.json format and `__init__.py` entry point
- [MODEL-CLASS.md](references/MODEL-CLASS.md) — Config/Model class hierarchy, required properties, predict/predict_all
- [DATALOADER.md](references/DATALOADER.md) — Multi-worker pickle compatibility, macOS restriction, platform-aware num_workers
- [LABEL-TYPES.md](references/LABEL-TYPES.md) — Label return types, coordinate normalization

## File Structure

A remote model zoo source is a directory containing:

```
my-model/
├── __init__.py       # Exports: download_model, load_model, resolve_input (all optional)
├── zoo.py            # Model classes, configs, inference logic
├── manifest.json     # Model metadata for zoo registration (REQUIRED)
└── README.md         # Usage docs (optional)
```

See [references/MANIFEST.md](references/MANIFEST.md) for manifest.json format and `__init__.py` exports. See [MODEL-CLASS.md](references/MODEL-CLASS.md) for the zoo.py class hierarchy and predict/predict_all patterns.

## Common Pitfalls

1. **Missing `name` in manifest.json** — FiftyOne silently skips manifests without a top-level `name` field. The remote source registration appears to succeed but the model isn't found.

2. **Custom picklable objects without platform-aware num_workers** — On macOS, custom classes from `zoo.py` in the DataLoader pickle cause `ModuleNotFoundError` in workers. Either use FiftyOne's built-in classes or gate `num_workers` on `sys.platform`. See [DATALOADER.md](references/DATALOADER.md).

3. **Returning dicts from image predict_all** — Creates `label_field_key` prefixed fields instead of storing under `label_field` directly. Breaks nested field paths. See [LABEL-TYPES.md](references/LABEL-TYPES.md).

4. **Wrong coordinate system** — VLMs often use non-standard coordinate orders or scales. Always verify the model's coordinate convention from concrete spatial examples in model documentation, not assumptions.

5. **Model card vs library docs** — HuggingFace model cards may show incorrect API usage (wrong model class, etc.). Always verify against the library's official documentation.

6. **Thinking mode + tool calling** — Models with thinking/reasoning modes may exhaust generation tokens before producing tool calls. Default to thinking OFF for structured operations.

## Quick Checklist

- [ ] `manifest.json` has top-level `name` field
- [ ] `__init__.py` uses relative imports (`from .zoo import ...`)
- [ ] Model inherits `fom.Model`, `fom.SamplesMixin`, `SupportsGetItem`, `TorchModelMixin`
- [ ] `collate_fn` and `GetItem` use FiftyOne built-ins, OR custom classes with platform-aware `num_workers`
- [ ] If using custom picklable objects, `num_workers=0` on macOS (`sys.platform == "darwin"`)
- [ ] `predict_all` handles PIL Image, filepath string, and dict inputs
- [ ] Image operations return single `fo.Label` instance, not dict
- [ ] Coordinates normalized to `[0, 1]` range
- [ ] Extra metadata stored as dynamic attributes on Labels

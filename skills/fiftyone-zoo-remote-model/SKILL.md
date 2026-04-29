---
name: fiftyone-zoo-remote-model
description: Use when integrating a model into FiftyOne's remote model zoo — detection, classification, segmentation, embedding, keypoint, or vision-language (VLM) models loaded via `register_zoo_model_source` and `load_zoo_model`, then applied with `dataset.apply_model`. Also for debugging zoo registration, `manifest.json` issues, custom `fom.Model` / `TorchModelMixin` subclasses, DataLoader pickle errors, or worker `ModuleNotFoundError` from spawned DataLoader workers.
allowed-tools: Read, Grep, Glob, Agent, WebFetch, Write, Edit
---

# FiftyOne Remote Model Zoo — Integration Guide

## When to use

Triggers: new remote zoo source; debugging an existing one; registration "succeeds" but model not loadable; `ModuleNotFoundError` from DataLoader workers; custom `fom.Model` / `TorchModelMixin`; VLM/structured-output integrations.

Not this skill: plugins, operators, panels, brain methods. Route via Phase 0.

## Phase 0 — Confirm the integration surface

| User wants to… | Surface | Skill |
|---|---|---|
| Apply a model (`dataset.apply_model`) | Remote zoo model | this skill |
| UI panels, buttons, side-effects | Plugin / operator | `fiftyone-develop-plugin` |
| Embeddings, similarity, uniqueness | Brain method | brain docs |

**Required output**: one-line confirmation. Example: "Zoo model integration because user wants `dataset.apply_model(model)` to write predictions." If you cannot write that line, stop.

## Phase 1 — Scaffold

Copy `template/`:

- `manifest.json` — top-level `name` required (silent skip if missing).
- `__init__.py` — exports `download_model`, `load_model`, optional `resolve_input`. Relative imports: `from .zoo import ...`.
- `zoo.py` — config + model class.

## Phase 2 — Implement

- Class hierarchy, properties, three-input predict dispatch → [MODEL-CLASS.md](references/MODEL-CLASS.md).
- Label return types, single-`fo.Label` rule, coordinates → [LABEL-TYPES.md](references/LABEL-TYPES.md).
- DataLoader pickle, worker import resolution → [DATALOADER.md](references/DATALOADER.md).
- **VLM / generative-structured-output** (uses `generate()` with prompts/schemas) → also [VLM-PATTERNS.md](references/VLM-PATTERNS.md).

## Phase 3 — Validate

- [ ] `manifest.json` has top-level `name`.
- [ ] `__init__.py` uses relative imports.
- [ ] Image ops return single `fo.Label` (dicts only for video frame-level, integer keys).
- [ ] One-known-example coordinate check passed.
- [ ] `dataset.apply_model(model)` runs with default `num_workers`.
- [ ] On macOS, run `dataset.apply_model(model, ...)` with default `num_workers` and confirm no `ModuleNotFoundError` from spawned workers.

**On failure**, route by symptom:

| Symptom | First look at |
|---|---|
| Registration "succeeds" but `load_zoo_model` fails | [MANIFEST.md](references/MANIFEST.md), [MODEL-CLASS.md](references/MODEL-CLASS.md) |
| `ModuleNotFoundError` / pickle error from workers | [DATALOADER.md](references/DATALOADER.md) |
| Predictions in unexpected fields or not stored | [LABEL-TYPES.md](references/LABEL-TYPES.md) |
| Spatial outputs (boxes/points) in wrong location | [LABEL-TYPES.md](references/LABEL-TYPES.md); VLM: [VLM-PATTERNS.md](references/VLM-PATTERNS.md) |
| Output is schema-correct but values are wrong | [DEBUGGING-PRINCIPLES.md](references/DEBUGGING-PRINCIPLES.md) — *Schema compliance ≠ correctness* |
| Backend / device error (OOM, op unimplemented) | [DEBUGGING-PRINCIPLES.md](references/DEBUGGING-PRINCIPLES.md) — *Document upstream constraints* |

## Key Directives

Canonical names; other files cite by name. Full failure modes and diagnostic moves in [DEBUGGING-PRINCIPLES.md](references/DEBUGGING-PRINCIPLES.md).

- **Framework-first.** ALWAYS use FiftyOne primitives before custom code. *Why:* framework classes are worker-importable; yours aren't.
- **Worker-pickle constraint.** NEVER define pickle-bound objects in `zoo.py`. *Why:* spawned DataLoader workers can't import modules loaded via `importlib.util.spec_from_file_location`.
- **Reference implementations need verification.** NEVER copy a pattern from another zoo source without running it under multi-worker first. *Why:* widely-copied references silently break.
- **Schema compliance ≠ correctness.** NEVER trust schema-conformant outputs as proof of correctness. *Why:* models echo your wrong field names back unchanged.
- **Read specs, don't patch parsers.** NEVER patch a parser more than twice — find the format spec. *Why:* each patch shifts the failure elsewhere; the cycle is unbounded.
- **Bounded repair scope.** NEVER grow repair logic past a few common malformations. *Why:* unbounded repair masks model-quality regressions.

## Quick reference index

- [MANIFEST.md](references/MANIFEST.md) — schema, entry points, idempotent `download_model`.
- [MODEL-CLASS.md](references/MODEL-CLASS.md) — hierarchy, properties, predict dispatch.
- [DATALOADER.md](references/DATALOADER.md) — worker pickle WHY, primitives, wrong fixes that look right.
- [LABEL-TYPES.md](references/LABEL-TYPES.md) — return types, coordinate normalization.
- [DEBUGGING-PRINCIPLES.md](references/DEBUGGING-PRINCIPLES.md) — six rules with failure modes and diagnostic moves.
- [VLM-PATTERNS.md](references/VLM-PATTERNS.md) — tool calling, generation budget, thinking, vision tokens, delimiters, multi-tier parser, coordinate quirks.

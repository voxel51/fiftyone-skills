# Debugging Principles

Six universal principles for remote zoo model integration. Each rule has a canonical name; other files cite them by that name.

## 1. Framework-first

**Rule.** Use FiftyOne's existing classes before defining your own.

**Failure mode.** Writing custom `collate_fn` and `GetItem` from scratch, then debugging pickle errors that the framework's classes do not have.

**Diagnostic move.** Before writing a class, search FiftyOne for an existing one with the same shape (`TorchModelMixin.collate_fn`, `fiftyone.utils.torch.ImageGetItem`).

## 2. Worker-pickle constraint

**Rule.** Anything pickled across a DataLoader worker boundary must resolve to a module the worker can import.

**Failure mode.** Code works locally with `num_workers=0`, fails in CI or on user machines with `ModuleNotFoundError` from spawned workers.

**Diagnostic move.** Run `apply_model` with default `num_workers` on macOS as a smoke test before shipping.

## 3. Reference implementations need verification

**Rule.** A pattern copied from another zoo source is not guaranteed correct.

**Failure mode.** Copying a pattern from a popular remote zoo source that itself does not support multi-worker.

**Diagnostic move.** Run multi-worker on the reference before copying its structure.

## 4. Schema compliance ≠ correctness

**Rule.** A model that conforms to your tool/JSON schema is not necessarily producing correct values.

**Failure mode.** Tool/JSON schema includes a field name the model has never seen; the model echoes it back; output looks correct but values are mis-mapped (e.g., bbox order silently swapped).

**Diagnostic move.** Verify outputs against ground-truth examples where the answer is known by inspection, not against schema validators.

## 5. Read specs, don't patch parsers

**Rule.** When a parser keeps breaking, find the format specification before iterating.

**Failure mode.** Regex after regex to handle "double commas", "unquoted keys", "fused quote patterns" — each fix shifts the failure.

**Diagnostic move.** When the second parser patch fails, stop. Find the format spec from upstream (transformers, vLLM, the model author's repo). 30 minutes spent reading saves a day of patching.

## 6. Bounded repair scope

**Rule.** Repair the few common malformations and stop.

**Failure mode.** Parsing-repair logic grows unboundedly to handle every observed malformation, masking real model-quality regressions.

**Diagnostic move.** Define the four most common malformations once. Beyond those, return empty rather than repair.

## Diagnostic discipline

- **Isolate variables when multiple things look broken.** Build a 2x2x... diagnostic that varies one factor at a time (e.g., thinking on/off x tools/no-tools x schema-A/schema-B). The discipline turns "parsing is broken" into n independent root causes.

- **Trust library docs over model cards.** Wrong-but-loadable model classes (`AutoModelFor*` mismatches) produce subtly wrong output without raising errors. When card and library disagree, the library is higher fidelity.

- **Document upstream constraints; don't work around them.** Some failures are framework / backend gaps (e.g., specific ops unimplemented on MPS). Surface in manifest `requirements` or README; do not write workaround code.

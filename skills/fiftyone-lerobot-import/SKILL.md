---
name: fiftyone-lerobot-import
description: Imports LeRobot v3 robot-learning datasets into FiftyOne as multimodal episode datasets using fo.types.LeRobotDataset, including downloading from Hugging Face Hub, detecting and converting v2.x datasets to v3, adding multiple sources with add_dir, and validating episode counts. Use when the user mentions LeRobot, lerobot/ HF dataset repos, robot episodes, teleop recordings, observation.state/action data, or wants robot learning data in FiftyOne.
---

# LeRobot Dataset Import for FiftyOne

Import a LeRobot v3 dataset into FiftyOne. One sample = one **episode**, not
one file. Follow the steps in order; the import is not done until validation
(Step 8) passes.

## Key Directives

1. **Build from directories, never from samples.** Use
   `fo.Dataset.from_dir(..., dataset_type=fo.types.LeRobotDataset)` for the
   first source and `dataset.add_dir(...)` for every additional source.
   `add_samples` cannot introduce a LeRobot source — samples carry a
   `media_reference` that only resolves through a source the dataset records,
   and unrecorded references are refused.
2. **v3 only.** `fo.types.LeRobotDataset` raises
   `UnsupportedLeRobotVersionError` on v2.x. Detect the version (Step 3) and
   convert (Step 4) before importing.
3. **The source must stay put.** Samples reference the source, they do not
   copy it. Never move, delete, or rewrite the LeRobot root after import; if
   it changes, re-import.
4. **STOP gate — packages:** never install a package without asking the user
   first (Step 5). Candidates: `pyarrow>=10.0.0` (import), `huggingface_hub`
   (download), `lerobot` (v2→v3 conversion only), `pypcd4` (only if
   `launch_app` raises `ModuleNotFoundError: pypcd4` — see Troubleshooting).
5. **STOP gate — creation:** never create the dataset until the user confirms
   the plan (Step 6). End the plan with a question and WAIT.
6. **Check name collisions** with `fo.list_datasets()` before creating. If it
   exists, ask: overwrite, rename, or abort. If no name was given, derive one
   from the repo id or folder (e.g. `lerobot/pusht` → `lerobot-pusht`),
   confirm it is unused, and tell the user.
7. **Always use absolute paths.**
8. **Datasets must be persistent** (`persistent=True`) unless told otherwise.
9. **Validate after import** (Step 8): imported episodes vs
   `meta/info.json` `total_episodes` (or the requested subset), and report
   `dataset.info["lerobot"]["skipped_episodes"]`.
10. **Keep error reports minimal** — one line on what failed and the fix.

## Complete Workflow

```
LeRobot Import Progress:
- [ ] Step 1: Identify the source (local path or HF repo id)
- [ ] Step 2: Download from Hugging Face Hub (if needed)
- [ ] Step 3: Inspect layout and detect version
- [ ] Step 4: Convert v2.x → v3 (if needed)
- [ ] Step 5: Packages (STOP gate)
- [ ] Step 6: Present plan, get confirmation (STOP gate)
- [ ] Step 7: Name check, import
- [ ] Step 8: Validate
- [ ] Step 9: Launch the App
```

## Step 1: Identify the source

- Looks like `owner/name` or a `huggingface.co/datasets/...` URL → HF Hub,
  go to Step 2.
- Local directory → skip to Step 3.
- Cloud URI (`s3://`, `gs://`) → download or mount it to a local directory
  first (e.g. `aws s3 sync`, `gsutil -m cp -r`, or a FUSE mount), then treat
  it as a local directory for every remaining step. The rest of this
  workflow (`meta/info.json` inspection, `from_dir(dataset_dir=...)`, and
  the absolute-paths rule) assumes a local filesystem path throughout.

## Step 2: Download from Hugging Face Hub

Hub repos tag format versions as revisions (`v2.1`, `v3.0`). Prefer the v3
revision when it exists; fall back to `main` and let Step 3 decide.

```bash
hf download <owner/name> --repo-type dataset --revision v3.0 \
    --local-dir /abs/path/lerobot/<name>
# if that revision does not exist:
hf download <owner/name> --repo-type dataset --local-dir /abs/path/lerobot/<name>
```

Large datasets: if only a subset is needed, note that the FiftyOne importer
still needs the full `meta/` directory plus whichever `data/` and `videos/`
shards hold the selected episodes. Download everything unless the user
explicitly accepts a partial import.

## Step 3: Inspect layout and detect version

```bash
cat /abs/path/lerobot/<name>/meta/info.json | python -c \
  "import json,sys; i=json.load(sys.stdin); print(i['codebase_version'], i['total_episodes'], i['fps'], i.get('robot_type')); print(list(i['features']))"
find /abs/path/lerobot/<name>/meta -maxdepth 2 | sort
```

| Signature | Version | Action |
|-----------|---------|--------|
| `codebase_version: v3.x`, `meta/episodes/chunk-*/file-*.parquet`, `meta/tasks.parquet`, `data/chunk-*/file-*.parquet` | v3 | Import (Step 5) |
| `codebase_version: v2.x`, `meta/episodes.jsonl`, `meta/tasks.jsonl`, `data/chunk-*/episode_*.parquet` | v2.x | Convert (Step 4) |
| No `meta/info.json` | not LeRobot | Stop; use `fiftyone-dataset-import` instead |

Record for the plan: episode count, fps, robot_type, camera features
(`dtype: video` or `image`), and `observation.state` / `action` shapes.

## Step 4: Convert v2.x → v3

Requires `lerobot` (STOP gate applies). The converter aggregates per-episode
files into shards, migrates JSONL metadata to Parquet, and rewrites
`info.json`. It does **not** push to the Hub when told so:

```bash
python -m lerobot.datasets.v30.convert_dataset_v21_to_v30 \
    --repo-id <owner/name> \
    --root /abs/path/lerobot/<name> \
    --push-to-hub=false
```

Older `lerobot` releases expose it as
`lerobot.scripts.convert_dataset_v21_to_v30`. After conversion, repeat
Step 3 and confirm `codebase_version` is `v3.x` before continuing.

## Step 5: Packages (STOP gate)

```bash
pip show pyarrow          # import; needs >=10.0.0
pip show huggingface_hub  # only if Step 2 was used
pip show lerobot          # only if Step 4 is needed
```

If anything is missing, STOP and ask before installing. Note: launching the
App also needs `pypcd4` on current FiftyOne dev builds
(`fiftyone.utils.utils3d` imports it at server start).

## Step 6: Present plan, get confirmation (STOP gate)

```
LeRobot Import Plan for /abs/path/lerobot/<name>:

Source:
  - codebase_version: v3.0 (converted from v2.1: no)
  - 200 episodes, 30 fps, robot_type: so100
  - cameras: observation.images.front (video, av1), observation.images.wrist (video, h264)
  - observation.state: 6 dims, action: 6 dims
  - tasks: 1 ("Pick up the cube")

Import:
  - Dataset name: <name>
  - Episodes: all (or: indexes [...] / max_samples N)
  - Persistent: yes
  - Additional sources to add_dir: none

Proceed with import? (yes/no)
```

**WAIT for the answer.**

## Step 7: Name check, import

```python
import fiftyone as fo

if "<name>" in fo.list_datasets():   # hard rule 6
    raise ValueError(
        "Dataset '<name>' already exists — ask the user to overwrite, "
        "rename, or abort before proceeding."
    )

dataset = fo.Dataset.from_dir(
    dataset_dir="/abs/path/lerobot/<name>",
    dataset_type=fo.types.LeRobotDataset,
    name="<name>",
    persistent=True,
    # optional subset controls (importer kwargs):
    # episodes=[0, 1, 2],   # explicit episode indexes
    # max_samples=50,
    # shuffle=True, seed=51,
)

# additional sources, each recorded on the dataset as it arrives
# dataset.add_dir(
#     dataset_dir="/abs/path/lerobot/<other>",
#     dataset_type=fo.types.LeRobotDataset,
# )
```

Import reads only `meta/info.json` and `meta/episodes/*.parquet`; no data
shard or video is opened, so it is fast even for large sources.

## Step 8: Validate

```python
import json
import fiftyone as fo

dataset = fo.load_dataset("<name>")
info = json.load(open("/abs/path/lerobot/<name>/meta/info.json"))

print("media_type:", dataset.media_type)                  # multimodal
print("episodes imported:", len(dataset), "/ source:", info["total_episodes"])
print("skipped:", dataset.info["lerobot"]["skipped_episodes"])
print("fields:", sorted(dataset.get_field_schema()))
print("tasks:", dataset.distinct("task"))
print("duration (s) bounds:", dataset.bounds("duration"))
```

Expected sample fields: `media_reference`, `episode_index`, `task`, `tasks`,
`length`, `duration`, `robot_type`, `fps`. If `len(dataset)` does not equal
`total_episodes` (or the requested subset) or `skipped_episodes` is
non-empty, report the numbers and the skipped-episode reasons — do not
declare success.

## Step 9: Launch the App

```python
session = fo.launch_app(dataset)
```

Point the user at the LeRobot-specific viewer features: Image tiles per
camera, **State & Action** tile, Plot tiles for any state/action dimension,
the **Streams** tab (Observations / Actions / Instructions / Custom), and the
**Statistics** tab in the right sidebar.

## Troubleshooting

| Symptom | Cause / fix |
|---------|-------------|
| `UnsupportedLeRobotVersionError: ... supports only v3.x` | v2.x source → Step 4 |
| `MalformedMediaSourceError: ... no episode metadata Parquet shards under meta/episodes` | v2.x layout (`episodes.jsonl`) → Step 4 |
| `MalformedMediaSourceError: LeRobot source is missing meta/info.json` | Wrong directory or partial download; point at the dataset root |
| `MissingMediaRootError` | Path does not exist or is relative; use an absolute path |
| `add_samples` refuses a sample | Hard rule 1: use `from_dir` / `add_dir` |
| `ModuleNotFoundError: pypcd4` on `launch_app` | `pip install pypcd4` (STOP gate) |
| Episodes listed under `skipped_episodes` | Malformed metadata rows in the source; report them, do not silently accept |
| Videos do not render in the App | Codec must be H.264 or AV1; check `info["features"][cam]["info"]["video.codec"]` |
| Samples broke after moving the source | Hard rule 3: re-import from the new location |

## Resources

- [LeRobot GitHub repository](https://github.com/huggingface/lerobot) — dataset format, v2→v3 conversion scripts
- [LeRobot dataset format docs](https://huggingface.co/docs/lerobot) — episode/chunk layout, `meta/info.json` schema
- [FiftyOne LLM Docs](https://docs.voxel51.com/llms.txt) — `fo.types.LeRobotDataset` and multimodal dataset APIs

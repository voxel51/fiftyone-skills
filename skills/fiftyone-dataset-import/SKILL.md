---
name: fiftyone-dataset-import
description: Imports datasets into FiftyOne with automatic format detection. Supports all media types (images, videos, point clouds, MCAP multimodal recordings), label formats (COCO, YOLO, VOC, KITTI), multimodal grouped datasets, LeRobot v3 robot-learning episode datasets, and Hugging Face Hub datasets. Use when importing datasets from local files or Hugging Face, loading autonomous driving data, importing robotics/AV sensor logs (MCAP, ROS bag), importing LeRobot robot-learning episodes (teleop recordings, observation.state/action data), or creating grouped datasets.
---

# Universal Dataset Import for FiftyOne

## Key Directives

**ALWAYS follow these rules:**

### 1. Scan folder FIRST
Before any import, deeply scan the directory to understand its structure:
```bash
# Use bash to explore
find /path/to/data -type f | head -50
ls -la /path/to/data
```

### 2. Auto-detect everything
Detect media types, label formats, and grouping patterns automatically. Never ask the user to specify format if it can be inferred.

### 3. Detect multimodal groups
Look for patterns that indicate grouped data:
- Scene folders containing multiple media files
- Filename patterns with common prefixes (e.g., `scene_001_left.jpg`, `scene_001_right.jpg`)
- Mixed media types that should be grouped (images + point clouds)

### 4. Detect and install required packages
Named autonomous-driving devkit formats (PandaSet, nuScenes, Waymo Open, Argoverse, KITTI 3D,
Lyft L5, A2D2) need an external Python package. Check with `pip show <package>`, ask the user
before installing, then verify with a smoke-test import. Full package table, directory-pattern
detection, and the complete conversion workflow are in
[SPECIALIZED-3D-FORMATS.md](SPECIALIZED-3D-FORMATS.md).

**No package is required to import or render MCAP (`.mcap`/`.bag`/`.rrd`) files.** The file
extension alone sets `media_type == "multimodal"`, and channel decoding and rendering happen
client-side in the FiftyOne App. Do not tell users to `pip install mcap` for this. The only
optional use for a Python-side package is reading channel schemas before opening the App, covered
in Step 9D below.

**Additional packages for 3D processing:** `open3d` (PCD conversion), `pyntcloud`, `laspy`
(LAS/LAZ). **For Hugging Face Hub:** `huggingface_hub`, `pyarrow`, `Pillow`.

### 5. Confirm before importing
Present findings to user and **explicitly ask for confirmation** before creating the dataset.
Always end your scan summary with a clear question like:
- "Proceed with import?"
- "Should I create the dataset with these settings?"

**Wait for user response before proceeding.** Do not create the dataset until the user confirms.

### 6. Check for existing datasets and generate names
Before creating a dataset, check if the proposed name already exists:
```python
list_datasets()
```
If the dataset name exists, ask the user:
- **Overwrite**: Delete existing and create new
- **Rename**: Use a different name (suggest alternatives like `dataset-name-v2`)
- **Abort**: Cancel the import

**If no dataset name was provided by the user**, generate a fun unique name using the pattern `{ADJECTIVE}_{NOUN}_{VERB}`:
- `squiggly_sky_floats`
- `droopy_horse_slams`
- `smooth_grass_grumbles`
- `nervous_hamburger_yodels`

Cross-check against `list_datasets()` to ensure uniqueness. **Always inform the user of the generated name before proceeding.**

### 7. Validate after import
Compare imported sample count with source file count. Report any discrepancies.

### 8. Report errors minimally to user
Keep error messages simple for the user. Use detailed error info internally to diagnose issues.

## Complete Workflow

**Before scanning, identify what kind of source this is** — most sources are local directories
and follow Steps 1-12 below, but two formats are detected up front instead of by scanning loose
files:

- A `lerobot/...` Hugging Face Hub repo id, or a local directory with `meta/info.json` at its
  root → LeRobot. Skip straight to [Step 9E](#step-9e-import-lerobot-robot-learning-datasets) and
  [LEROBOT-IMPORT.md](LEROBOT-IMPORT.md); do not run Step 1's folder scan on a bare repo id first
  since there is nothing local to scan until it's downloaded.
- Any other Hugging Face Hub repo id (`owner/name`) or `huggingface.co/datasets/...` URL → see
  [Importing from Hugging Face Hub](#importing-from-hugging-face-hub) below.
- A local directory of `.mcap`/`.bag`/`.rrd` files → Steps 1-8 apply for the scan/confirm/create
  steps, then jump to [Step 9D](#step-9d-import-multimodal-mcap-recordings) for the import itself.
- Everything else (a local path to images, videos, point clouds, or an existing label format) →
  continue with Step 1.

### Step 1: Deep Folder Scan

Scan the target directory to understand its structure:

```bash
# Count files by extension
find /path/to/data -type f | sed 's/.*\.//' | sort | uniq -c | sort -rn

# List directory structure (2 levels deep)
find /path/to/data -maxdepth 2 -type d

# Sample some files
ls -la /path/to/data/* | head -20

# IMPORTANT: Scan for ALL annotation/label directories
ls -la /path/to/data/annotations/ 2>/dev/null || ls -la /path/to/data/labels/ 2>/dev/null
```

Build an inventory of:
- Media files by type (images, videos, point clouds, 3D)
- Label files by format (JSON, XML, TXT, YAML, PKL)
- Directory structure (flat vs nested vs scene-based)
- **ALL annotation types present** (cuboids, segmentation, tracking, etc.)

**For 3D/Autonomous Driving datasets, specifically check:**
```bash
# List all annotation subdirectories
find /path/to/data -type d -name "annotations" -o -name "labels" | xargs -I {} ls -la {}

# Sample an annotation file to understand its structure
python3 -c "import pickle, gzip; print(pickle.load(gzip.open('path/to/annotation.pkl.gz', 'rb'))[:2])"
```

### Step 2: Identify Media Types

Classify files by extension:

| Extensions | Media Type | FiftyOne Type |
|------------|------------|---------------|
| `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.webp`, `.tiff` | Image | `image` |
| `.mp4`, `.avi`, `.mov`, `.mkv`, `.webm` | Video | `video` |
| `.pcd`, `.ply`, `.las`, `.laz` | Point Cloud | `point-cloud` |
| `.fo3d`, `.obj`, `.gltf`, `.glb` | 3D Scene | `3d` |
| `.mcap`, `.bag`, `.rrd` | Multimodal (robotics/AV sensor log) | `multimodal` |

**MCAP recordings are a special case.** A single `.mcap` file is one self-contained multimodal
episode that can hold many time-synchronized streams internally (camera images, LIDAR, IMU, GPS,
transforms, diagnostics), each as its own channel/topic. There is no separate MCAP dataset type and
no labels file to import: one `.mcap` file is one sample. See
[Step 9D](#step-9d-import-multimodal-mcap-recordings) below.

**LeRobot datasets are also a special case.** A LeRobot source is a directory (or `lerobot/...`
Hugging Face Hub repo) with `meta/info.json` at its root, not a pile of loose media files — do not
scan it file-by-file like the patterns above. One sample = one **episode**, built with
`fo.Dataset.from_dir(..., dataset_type=fo.types.LeRobotDataset)`, never `add_samples`. See
[Step 9E](#step-9e-import-lerobot-robot-learning-datasets) below.

### Step 3: Detect Label Format

Identify label format from file patterns:

| Pattern | Format | Dataset Type |
|---------|--------|--------------|
| `annotations.json` or `instances*.json` with COCO structure | COCO | `COCO` |
| `*.xml` files with Pascal VOC structure | VOC | `VOC` |
| `*.txt` per image + `classes.txt` | YOLOv4 | `YOLOv4` |
| `data.yaml` + `labels/*.txt` | YOLOv5 | `YOLOv5` |
| `*.txt` per image (KITTI format) | KITTI | `KITTI` |
| Single `annotations.xml` (CVAT format) | CVAT | `CVAT Image` |
| `*.json` with OpenLABEL structure | OpenLABEL | `OpenLABEL Image` |
| Folder-per-class structure | Classification | `Image Classification Directory Tree` |
| `*.csv` with filepath column | CSV | `CSV` |
| `*.json` with GeoJSON structure | GeoJSON | `GeoJSON` |
| `.dcm` DICOM files | DICOM | `DICOM` |
| `.tiff` with geo metadata | GeoTIFF | `GeoTIFF` |
| `meta/info.json` + `meta/episodes/*.parquet` at the source root (or a `lerobot/...` HF repo) | LeRobot | `LeRobotDataset` |

**LeRobot robot-learning datasets** are directory-based, not file-based: detect them by the
presence of `meta/info.json` at the source root (or an HF repo id under the `lerobot/` namespace)
before falling back to any of the patterns above. There is no labels file to import separately —
episodes, tasks, and `observation.state`/`action` data all come from the LeRobot importer. See
[Step 9E](#step-9e-import-lerobot-robot-learning-datasets).

**Specialized autonomous driving formats** (PandaSet, nuScenes, Waymo Open, Argoverse, KITTI 3D,
Lyft L5, A2D2) need an external devkit and a conversion step. See
[SPECIALIZED-3D-FORMATS.md](SPECIALIZED-3D-FORMATS.md) for directory-pattern detection, the
package table, and the complete conversion workflow.

### Step 4: Detect Required Packages

Check whether the detected format's package is already installed (`pip show <package>`), inform
the user what's needed and why, ask permission before installing, then verify with a smoke-test
import. Full detail in [SPECIALIZED-3D-FORMATS.md](SPECIALIZED-3D-FORMATS.md).

### Step 5: Detect Grouping Pattern

Determine if data should be grouped:

**Pattern A: Scene Folders (Most Common for Multimodal)**
```
/data/
├── scene_001/
│   ├── left.jpg
│   ├── right.jpg
│   ├── lidar.pcd
│   └── labels.json
├── scene_002/
│   └── ...
```
Detection: Each subfolder = one group, files inside = slices

**Pattern B: Filename Prefix**
```
/data/
├── 001_left.jpg
├── 001_right.jpg
├── 001_lidar.pcd
├── 002_left.jpg
├── 002_right.jpg
├── 002_lidar.pcd
```
Detection: Common prefix = group ID, suffix = slice name

**Pattern C: No Grouping (Flat)**
```
/data/
├── image_001.jpg
├── image_002.jpg
├── image_003.jpg
```
Detection: Single media type, no clear grouping pattern

**Pattern D: MCAP Multimodal Recordings (No Grouping Needed)**
```
/data/
├── episode-0001.mcap
├── episode-0002.mcap
├── episode-0003.mcap
```
Detection: Each `.mcap`/`.bag`/`.rrd` file is already a self-contained multimodal recording
(cameras, LIDAR, IMU, GPS, etc. are internal channels within the file). Do **not** try to group
these with other files — import each recording as a single sample. See
[Step 9D](#step-9d-import-multimodal-mcap-recordings).

### Step 6: Present Findings to User

Before importing, present a clear summary that includes **ALL detected labels**:

```
Scan Results for /path/to/data:

Media Found:
  - 3,000 images (.jpg, .png)
  - 1,000 point clouds (.pkl.gz → will convert to .pcd)
  - 0 videos

Grouping Detected:
  - Pattern: Scene folders
  - Groups: 1,000 scenes
  - Slices: left (image), right (image), front (image), lidar (point-cloud)

ALL Labels Detected:
  ├── cuboids/           (3D bounding boxes, 1,000 files)
  │   └── Format: pickle, Fields: label, position, dimensions, rotation, track_id
  ├── semseg/            (Semantic segmentation, 1,000 files)
  │   └── Format: pickle, point-wise class labels
  └── instances.json     (2D detections, COCO format)
      └── Classes: 10 (car, pedestrian, cyclist, ...)

Required Packages:
  - ✅ pandaset (installed)
  - ⚠️ open3d (needed for PCD conversion) → pip install open3d

Proposed Configuration:
  - Dataset name: my-dataset
  - Type: Grouped (multimodal)
  - Default slice: front_camera
  - Labels to import:
    - detections_3d (from cuboids/)
    - point_labels (from semseg/)
    - detections (from instances.json)

Proceed with import? (yes/no)
```

**IMPORTANT:**
- List ALL annotation types found during the scan
- Show the format/structure of each label type
- Indicate which labels will be imported and how
- Wait for user confirmation before proceeding

### Step 7: Check for Existing Dataset and Generate Name

Before creating, check if the dataset name already exists:

```python
# Check existing datasets
list_datasets()
```

**If the user didn't provide a name**, generate one using the `{ADJECTIVE}_{NOUN}_{VERB}` pattern (e.g., `smooth_grass_grumbles`). Cross-check against `list_datasets()` for uniqueness. **Always inform the user of the generated name before proceeding.**

If the proposed dataset name exists in the list:
1. Inform the user: "A dataset named 'my-dataset' already exists with X samples."
2. Ask for their preference:
   - **Overwrite**: Delete existing dataset first
   - **Rename**: Suggest alternatives (e.g., `my-dataset-v2`, `my-dataset-20240107`)
   - **Abort**: Cancel the import

If user chooses to overwrite:
```python
# Delete existing dataset
set_context(dataset_name="my-dataset")
execute_operator(
    operator_uri="@voxel51/utils/delete_dataset",
    params={"name": "my-dataset"}
)
```

### Step 8: Create Dataset

```python
# Create the dataset
execute_operator(
    operator_uri="@voxel51/utils/create_dataset",
    params={
        "name": "my-dataset",
        "persistent": true
    }
)

# Set context
set_context(dataset_name="my-dataset")
```

### Step 9A: Import Simple Dataset (No Groups)

For flat datasets without grouping:

```python
# Import media only
execute_operator(
    operator_uri="@voxel51/io/import_samples",
    params={
        "import_type": "MEDIA_ONLY",
        "style": "DIRECTORY",
        "directory": {"absolute_path": "/path/to/images"}
    }
)

# Import with labels
execute_operator(
    operator_uri="@voxel51/io/import_samples",
    params={
        "import_type": "MEDIA_AND_LABELS",
        "dataset_type": "COCO",
        "data_path": {"absolute_path": "/path/to/images"},
        "labels_path": {"absolute_path": "/path/to/annotations.json"},
        "label_field": "ground_truth"
    }
)
```

### Step 9B: Import Grouped Dataset (Multimodal)

For multimodal data with groups, use Python directly. Guide the user:

```python
import fiftyone as fo

# Create dataset
dataset = fo.Dataset("multimodal-dataset", persistent=True)

# Add group field
dataset.add_group_field("group", default="front")

# Create samples for each group
import os
from pathlib import Path

data_dir = Path("/path/to/data")
samples = []

for scene_dir in sorted(data_dir.iterdir()):
    if not scene_dir.is_dir():
        continue

    # Create a group for this scene
    group = fo.Group()

    # Add each file as a slice
    for file in scene_dir.iterdir():
        if file.suffix in ['.jpg', '.png']:
            # Determine slice name from filename
            slice_name = file.stem  # e.g., "left", "right", "front"
            samples.append(fo.Sample(
                filepath=str(file),
                group=group.element(slice_name)
            ))
        elif file.suffix == '.pcd':
            samples.append(fo.Sample(
                filepath=str(file),
                group=group.element("lidar")
            ))
        elif file.suffix == '.mp4':
            samples.append(fo.Sample(
                filepath=str(file),
                group=group.element("video")
            ))

# Add all samples
dataset.add_samples(samples)
print(f"Added {len(dataset)} samples in {len(dataset.distinct('group.id'))} groups")
```

### Step 9C: Import Specialized Format Dataset (3D/Autonomous Driving)

For datasets requiring an external devkit (PandaSet, nuScenes, Waymo, Argoverse, KITTI 3D, Lyft
L5, A2D2), use the devkit to load the raw data, convert point clouds to PCD, build `fo.Scene`
objects for 3D visualization, and import every detected label type (cuboids, segmentation,
tracking). The full workflow, PCD conversion code, label-type mapping, and a complete worked
PandaSet example are in [SPECIALIZED-3D-FORMATS.md](SPECIALIZED-3D-FORMATS.md).

### Step 9D: Import Multimodal (MCAP) Recordings

MCAP is the container format FiftyOne uses for time-synchronized robotics and autonomous vehicle
sensor logs (camera images, LIDAR/point clouds, IMU, GPS, coordinate frame transforms,
diagnostics, and more, all as channels/topics inside one file). Unlike the specialized 3D formats
above, **no devkit, no label conversion, and no extra Python package are required on the import
side** — the sample's `filepath` extension alone is enough for FiftyOne to classify it as
`media_type == "multimodal"`; decoding channel schemas (ROS 1/2, Foxglove, JSON) and rendering the
tiled viewer happens entirely client-side in the App when the sample is opened.

**This section covers the common case: you already have working `.mcap` files and just need them
in a dataset.** For anything deeper, three linked reference files carry the rest. Read the one that
matches what's actually happening:

| Situation | Read |
|---|---|
| A tile isn't rendering, or the App "looks broken" | [MCAP-TROUBLESHOOTING.md](MCAP-TROUBLESHOOTING.md). Check its symptom table before assuming a bug: the viewer fails silently by design when a schema isn't decodable, so most reports of "the import isn't working" turn out not to be import bugs at all |
| Authoring `.mcap` from raw sensor data (ROS bags, Zarr, HDF5, PCD, CSV, image folders) with `foxglove-sdk`, or converting/merging/splitting/patching existing MCAP files | [MCAP-AUTHORING.md](MCAP-AUTHORING.md) |
| Building the FiftyOne dataset from finished episodes, or about to declare an import done | [MCAP-DATASET-AND-VALIDATION.md](MCAP-DATASET-AND-VALIDATION.md) |

**1. Import.** Each `.mcap` file becomes exactly one sample. No package install step is needed.
Use the same `MEDIA_ONLY` + glob pattern approach as Use Case 3 (point clouds):

```python
execute_operator(
    operator_uri="@voxel51/utils/create_dataset",
    params={"name": "robot-teleop-episodes", "persistent": true}
)

set_context(dataset_name="robot-teleop-episodes")

execute_operator(
    operator_uri="@voxel51/io/import_samples",
    params={
        "import_type": "MEDIA_ONLY",
        "style": "GLOB_PATTERN",
        "glob_patt": {"absolute_path": "/path/to/recordings/*.mcap"}
    }
)
```

Or directly in Python, for more control (e.g. tagging episodes by source, adding custom metadata
fields extracted from the filename):

```python
import fiftyone as fo
from pathlib import Path

dataset = fo.Dataset("robot-teleop-episodes", persistent=True)

recordings_dir = Path("/path/to/recordings")
samples = [
    fo.Sample(filepath=str(mcap_file))
    for mcap_file in sorted(recordings_dir.glob("*.mcap"))
]

dataset.add_samples(samples)

print(dataset.media_type)  # "multimodal"
```

**2. Do not group MCAP samples with other slices.** Each `.mcap` file already carries all of its
sensor streams internally. Adding it as one slice in a `fo.Group()` alongside separately exported
camera or LiDAR files would duplicate data that's already inside the recording.

**2b. Detect capabilities by schema, not by topic name, and store them as fields.** A topic's name
is not a reliable signal for what it renders as. A topic named `/livox/lidar` or
`/os_node/imu_packets` looks like LiDAR or IMU data, but if its actual message schema is a
vendor-specific format (Livox's `livox_ros_driver/msg/CustomMsg`, or Ouster's raw
`ouster_ros/msg/PacketMsg`), FiftyOne has no built-in decoder for it. It will never render in the
3D or Plot tile no matter how the topic is named, and always falls back to the raw Message tile.
Only a fixed set of schemas render in each tile type. See
[MCAP-TROUBLESHOOTING.md's schema-to-tile table](MCAP-TROUBLESHOOTING.md#schema-to-tile-reference)
for the full list; a custom or proprietary LiDAR message is not on it and is expected to stay in
the Message tile.

Check real schemas from the file with the lightweight `mcap` package (`pip install mcap`, a small
pure-Python reader unrelated to any ROS install) and store the result as boolean fields
(`has_pointcloud`, `has_image`, `has_gps`, `has_imu`, and so on) so users and agents can query
capability across many recordings without opening each one in the App. Use the full
`mcap_stats()`/`build_sample()` helper in
[MCAP-DATASET-AND-VALIDATION.md](MCAP-DATASET-AND-VALIDATION.md#capability-flags-from-schemas-not-topic-names)
rather than reimplementing a narrower version. It also captures `duration_s`, `message_count`,
`topics`, and `schemas` needed for validation in the same pass, and answers "will this file show a
point cloud" with `dataset.match(F("has_pointcloud"))` instead of opening every sample to find out.

**3. Validate.** Confirm `dataset.media_type == "multimodal"` and that the sample count matches the
number of recording files found during the scan. Individual channels, topics, annotations, and time
tracks are inspected in the App's multimodal viewer, not via the Python import step. For anything
beyond a handful of files, also run the cheap `validate_mcap()` structural check in
[MCAP-DATASET-AND-VALIDATION.md](MCAP-DATASET-AND-VALIDATION.md#a-written-file-is-not-a-good-file).
A file can pass every count-based check here while being silently corrupted in a way that only
surfaces when a sample is actually opened.

**4. Launch the App** to explore streams. FiftyOne opens multimodal samples in a tiled viewer
(image, 3D, map, plot, message, and log tiles) with a shared playback clock:

```python
launch_app(dataset_name="robot-teleop-episodes")
```

**Note on "no data" at the start of playback:** the Message, Plot, 3D, and Map tiles all show the
most recent message as of the current playhead. If a topic's first message doesn't start at `t=0`
(common, since sensors have startup lag), a tile bound to it will legitimately show nothing, for
example "No message at or before the playhead on this topic," until playback is scrubbed or played
past that topic's first timestamp. This is expected behavior, not a broken import. Verify by
pressing play or scrubbing forward before concluding a tile is broken. If a tile still looks wrong
after that, check [MCAP-TROUBLESHOOTING.md](MCAP-TROUBLESHOOTING.md)'s symptom table before
assuming the import failed.

**Note:** temporal tags (tags on a time interval within a recording, added with
`dataset.temporal_tags.add(...)`) work locally with no Enterprise requirement. See
[MCAP-DATASET-AND-VALIDATION.md](MCAP-DATASET-AND-VALIDATION.md#temporal-tags) for the pattern.
MCAP indexing, which projects channels into queryable Parquet tables for cross-recording search, is
an Enterprise-only feature and out of scope for a local import. See the
[FiftyOne Multimodal guide](https://docs.voxel51.com/user_guide/multimodal.html) if a user asks
about it.

### Step 9E: Import LeRobot Robot-Learning Datasets

LeRobot is a directory-based robot-learning dataset format (local, or downloaded from a
Hugging Face Hub `lerobot/...` repo, e.g. `lerobot/aloha_sim_insertion_human`). One sample = one
**episode**, not one file, and `fo.types.LeRobotDataset` only supports the v3 layout.

**Full workflow, STOP gates, and troubleshooting are in
[LEROBOT-IMPORT.md](LEROBOT-IMPORT.md) — read it before importing a LeRobot source.** Summary:

1. Identify the source (local path or HF repo id) and download it if it's on the Hub.
2. Inspect `meta/info.json` and detect `codebase_version`; convert v2.x → v3 with `lerobot`'s
   converter if needed (`fo.types.LeRobotDataset` raises `UnsupportedLeRobotVersionError` on v2.x).
3. **STOP gate:** confirm required packages (`pyarrow>=10.0.0`, `huggingface_hub`, `lerobot`) before
   installing anything.
4. **STOP gate:** present the import plan (episode count, fps, robot_type, camera/state/action
   shapes) and wait for confirmation before creating the dataset.
5. Check name collisions with `fo.list_datasets()`, then import:

```python
import fiftyone as fo

dataset = fo.Dataset.from_dir(
    dataset_dir="/abs/path/lerobot/<name>",
    dataset_type=fo.types.LeRobotDataset,
    name="<name>",
    persistent=True,
)
```

6. Validate imported episode count against `meta/info.json`'s `total_episodes` and report
   `dataset.info["lerobot"]["skipped_episodes"]` — do not declare success if either mismatches.
7. Launch the App: episodes render with per-camera Image tiles, a **State & Action** tile, Plot
   tiles for state/action dimensions, and a **Streams** tab.

Use `add_samples` for nothing here — it cannot introduce a LeRobot source. Use
`dataset.add_dir(..., dataset_type=fo.types.LeRobotDataset)` to add further LeRobot sources to an
existing dataset.

### Step 10: Import Additional Labels (Optional)

If labels weren't imported with the specialized format, add them separately:

```python
# For COCO labels that reference filepaths
execute_operator(
    operator_uri="@voxel51/io/import_samples",
    params={
        "import_type": "LABELS_ONLY",
        "dataset_type": "COCO",
        "labels_path": {"absolute_path": "/path/to/annotations.json"},
        "label_field": "ground_truth"
    }
)
```

### Step 11: Validate Import

```python
# Load and verify
load_dataset(name="my-dataset")

# Check counts match
dataset_summary(name="my-dataset")
```

Compare:
- Imported samples vs source files
- Groups created vs expected
- Labels imported vs annotation count

### Step 12: Launch App and View

```python
launch_app(dataset_name="my-dataset")

# For grouped datasets, view different slices
# In the App, use the slice selector dropdown
```

## Supported Dataset Types

### Media Types

| Type | Extensions | Description |
|------|------------|-------------|
| `image` | `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.webp`, `.tiff` | Static images |
| `video` | `.mp4`, `.avi`, `.mov`, `.mkv`, `.webm` | Video files with frames |
| `point-cloud` | `.pcd`, `.ply`, `.las`, `.laz` | 3D point cloud data |
| `3d` | `.fo3d`, `.obj`, `.gltf`, `.glb` | 3D scenes and meshes |
| `multimodal` | `.mcap`, `.bag`, `.rrd` | Time-synchronized robotics/AV sensor recordings (MCAP container format) |

### Label Formats

| Format | Dataset Type Value | Label Types | File Pattern |
|--------|-------------------|-------------|--------------|
| COCO | `COCO` | detections, segmentations, keypoints | `*.json` |
| VOC/Pascal | `VOC` | detections | `*.xml` per image |
| KITTI | `KITTI` | detections | `*.txt` per image |
| YOLOv4 | `YOLOv4` | detections | `*.txt` + `classes.txt` |
| YOLOv5 | `YOLOv5` | detections | `data.yaml` + `labels/*.txt` |
| CVAT Image | `CVAT Image` | classifications, detections, polylines, keypoints | Single `*.xml` |
| CVAT Video | `CVAT Video` | frame labels | XML directory |
| OpenLABEL Image | `OpenLABEL Image` | all types | `*.json` directory |
| OpenLABEL Video | `OpenLABEL Video` | all types | `*.json` directory |
| TF Object Detection | `TF Object Detection` | detections | TFRecords |
| TF Image Classification | `TF Image Classification` | classification | TFRecords |
| Image Classification Tree | `Image Classification Directory Tree` | classification | Folder per class |
| Video Classification Tree | `Video Classification Directory Tree` | classification | Folder per class |
| Image Segmentation | `Image Segmentation` | segmentation | Mask images |
| CSV | `CSV` | custom fields | `*.csv` |
| DICOM | `DICOM` | medical metadata | `.dcm` files |
| GeoJSON | `GeoJSON` | geolocation | `*.json` |
| GeoTIFF | `GeoTIFF` | geolocation | `.tiff` with geo |
| FiftyOne Dataset | `FiftyOne Dataset` | all types | Exported format |
| LeRobot | `LeRobotDataset` | episode metadata (task, state, action, duration) | `meta/info.json` + `meta/episodes/*.parquet` |

## Common Use Cases

Copy-paste starting points for COCO, YOLO, point clouds, autonomous driving groups, classification
trees, and mixed media are in [USE-CASE-EXAMPLES.md](USE-CASE-EXAMPLES.md).

## Working with Groups

### Understanding Group Structure

In a grouped dataset:
- Each **group** represents one scene/moment (e.g., one timestamp)
- Each **slice** represents one modality (e.g., left camera, lidar)
- All samples in a group share the same `group.id`
- Each sample has a `group.name` indicating its slice

```python
# Access group information
print(dataset.group_slices)        # ['front_camera', 'left_camera', 'lidar']
print(dataset.group_media_types)   # {'front_camera': 'image', 'lidar': 'point-cloud'}
print(dataset.default_group_slice) # 'front_camera'

# Iterate over groups
for group in dataset.iter_groups():
    print(f"Group has {len(group)} slices")
    for slice_name, sample in group.items():
        print(f"  {slice_name}: {sample.filepath}")

# Get specific slice view
front_images = dataset.select_group_slices("front_camera")
all_point_clouds = dataset.select_group_slices(media_type="point-cloud")
```

### Viewing Groups in the App

After launching the app:
1. The slice selector dropdown appears in the top bar
2. Select different slices to view each modality
3. Samples are synchronized - selecting a sample shows all its group members
4. Use the grid view to see multiple slices side by side

## Importing from Hugging Face Hub

For complete HF Hub import documentation, see [HF-HUB-IMPORT.md](HF-HUB-IMPORT.md).

**Quick reference:**

| Dataset Type | Method |
|--------------|--------|
| FiftyOne-formatted (`fiftyone.yml`) | `load_from_hub("repo_id")` |
| Parquet-based | `load_from_hub("repo_id", format="ParquetFilesDataset", filepath="image")` |
| COCO/YOLO/VOC on HF | `snapshot_download()` → local import |
| Rate limited (>10K) | Parquet extraction fallback (see HF-HUB-IMPORT.md) |
| LeRobot (`lerobot/...`) | `hf download` then `fo.Dataset.from_dir(..., dataset_type=fo.types.LeRobotDataset)` — see [Step 9E](#step-9e-import-lerobot-robot-learning-datasets) |

**Quick start:**
```python
from fiftyone.utils.huggingface import load_from_hub

# FiftyOne-formatted dataset
dataset = load_from_hub("Voxel51/VisDrone2019-DET", persistent=True)

# Generic parquet dataset
dataset = load_from_hub(
    "username/dataset",
    format="ParquetFilesDataset",
    filepath="image",
    classification_fields="label",
    persistent=True,
)
```

**LeRobot repos (`lerobot/...`) are the exception** — do not route them through `load_from_hub()`.
Download with `hf download` and import with `fo.Dataset.from_dir(..., dataset_type=fo.types.LeRobotDataset)`
instead. See [Step 9E](#step-9e-import-lerobot-robot-learning-datasets) and
[LEROBOT-IMPORT.md](LEROBOT-IMPORT.md).

## Troubleshooting

**Error: "Dataset already exists"**
- Use a different dataset name
- Or delete existing: `execute_operator("@voxel51/utils/delete_dataset", {"name": "dataset-name"})`

**Error: "No samples found"**
- Verify directory path is correct and accessible
- Check file extensions are supported
- For nested directories, ensure recursive scanning

**Error: "Labels path not found"**
- Verify labels file/directory exists
- Check path is absolute, not relative
- Ensure correct format is detected

**Error: "Invalid group configuration"**
- Each group must have at least one sample
- Slice names must be consistent across groups
- Only one `3d` slice allowed per group

**Import is slow**
- For large datasets, use delegated execution
- Import in batches if needed
- Consider using glob patterns to filter files

**Point clouds not rendering**
- Ensure `.pcd` files are valid
- Check FiftyOne 3D visualization is enabled
- Verify point cloud plugin is installed

**MCAP sample added but `dataset.media_type` isn't `"multimodal"`**
- Confirm the filepath extension is exactly `.mcap`, `.bag`, or `.rrd` (lowercase)
- A dataset's media type reflects the extensions of *all* its samples — mixing `.mcap` files with
  images/videos in the same (non-grouped) dataset will raise a media type conflict; keep MCAP
  recordings in their own dataset or group slice

**A multimodal tile (Image/3D/Map/Plot/Logs) isn't rendering what you expect**
- This is almost never a broken import — the viewer fails silently by design when a schema isn't
  decodable or a topic's data doesn't start at `t=0`. Check
  [MCAP-TROUBLESHOOTING.md](MCAP-TROUBLESHOOTING.md)'s symptom table first
- If you're authoring, converting, or patching the `.mcap` files themselves (not just importing
  existing ones), see [MCAP-AUTHORING.md](MCAP-AUTHORING.md) instead

**Groups not detected**
- Check folder structure matches expected patterns
- Verify consistent naming across scenes
- May need to specify grouping manually

**`UnsupportedLeRobotVersionError` or `MalformedMediaSourceError` on a LeRobot source**
- The source is v2.x (`meta/episodes.jsonl` instead of `meta/episodes/*.parquet`) — convert to v3
  first. See [LEROBOT-IMPORT.md](LEROBOT-IMPORT.md)'s Step 4 and full troubleshooting table
- `add_samples` cannot introduce a LeRobot source — use `from_dir` / `add_dir` with
  `dataset_type=fo.types.LeRobotDataset`

## Best Practices

1. **Always scan first** - Understand the data before importing
2. **Confirm with user** - Present findings before creating dataset
3. **Use descriptive names** - Dataset names and label fields should be meaningful
4. **Validate counts** - Ensure imported samples match source files
5. **Handle errors gracefully** - Report issues clearly, continue with valid files
6. **Use groups for multimodal** - Don't flatten data that should be grouped
7. **Set appropriate default slice** - Choose the most commonly viewed modality
8. **Tag imports** - Use tags to track import batches or sources

## Performance Notes

**Import time estimates:**
- 1,000 images: ~10-30 seconds
- 10,000 images: ~2-5 minutes
- 100,000 images: ~20-60 minutes
- Point clouds: ~2x slower than images
- Videos: Depends on frame extraction settings

**Memory requirements:**
- ~1KB per sample metadata
- Media files are referenced, not loaded into memory
- Large datasets may require increased MongoDB limits

## Resources

- [FiftyOne Dataset Import Guide](https://docs.voxel51.com/user_guide/dataset_creation/index.html)
- [Grouped Datasets Guide](https://docs.voxel51.com/user_guide/groups.html)
- [Point Cloud Support](https://docs.voxel51.com/user_guide/3d.html)
- [FiftyOne Multimodal (MCAP) Guide](https://docs.voxel51.com/user_guide/multimodal.html)
- [Supported Dataset Formats](https://docs.voxel51.com/user_guide/dataset_creation/datasets.html)
- [FiftyOne I/O Plugin](https://github.com/voxel51/fiftyone-plugins/tree/main/plugins/io)
- [FiftyOne Hugging Face Integration](https://docs.voxel51.com/integrations/huggingface.html)
- [Hugging Face Hub Documentation](https://huggingface.co/docs/hub/index)
- [LeRobot GitHub repository](https://github.com/huggingface/lerobot) — dataset format, v2→v3 conversion scripts
- [LeRobot dataset format docs](https://huggingface.co/docs/lerobot) — episode/chunk layout, `meta/info.json` schema

This skill directory ships reference files read on demand rather than every invocation:

- [HF-HUB-IMPORT.md](HF-HUB-IMPORT.md): Hugging Face Hub specifics
- [SPECIALIZED-3D-FORMATS.md](SPECIALIZED-3D-FORMATS.md): PandaSet/nuScenes/Waymo/Argoverse/KITTI
  3D/Lyft L5/A2D2 devkit workflow
- [USE-CASE-EXAMPLES.md](USE-CASE-EXAMPLES.md): copy-paste starting points for common import shapes
- [MCAP-TROUBLESHOOTING.md](MCAP-TROUBLESHOOTING.md): symptom table and why a tile isn't rendering
- [MCAP-AUTHORING.md](MCAP-AUTHORING.md): authoring MCAP from raw data, converting ROS bags, merging/patching
- [MCAP-DATASET-AND-VALIDATION.md](MCAP-DATASET-AND-VALIDATION.md): capability flags, validation,
  process discipline for MCAP imports
- [LEROBOT-IMPORT.md](LEROBOT-IMPORT.md): full LeRobot workflow — HF Hub download, v2.x → v3
  conversion, STOP gates, validation, and troubleshooting


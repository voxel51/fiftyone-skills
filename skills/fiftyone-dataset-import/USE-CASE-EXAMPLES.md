# Use case examples

Copy-paste starting points for common import shapes. Each assumes the scan and format detection
in `SKILL.md` steps 1 to 7 are already done and the user confirmed. For MCAP recordings, see
[SKILL.md's Step 9D](SKILL.md#step-9d-import-multimodal-mcap-recordings). For PandaSet/nuScenes/
Waymo/Argoverse/KITTI 3D/Lyft L5/A2D2, see [SPECIALIZED-3D-FORMATS.md](SPECIALIZED-3D-FORMATS.md).

## Contents

1. [Simple image dataset with COCO labels](#1-simple-image-dataset-with-coco-labels)
2. [YOLO dataset](#2-yolo-dataset)
3. [Point cloud dataset](#3-point-cloud-dataset)
4. [Autonomous driving, multimodal groups](#4-autonomous-driving-multimodal-groups)
5. [Classification directory tree](#5-classification-directory-tree)
6. [Mixed media, images and videos](#6-mixed-media-images-and-videos)

## 1. Simple image dataset with COCO labels

```python
# Found: 5000 images, annotations.json (COCO format)

execute_operator(
    operator_uri="@voxel51/utils/create_dataset",
    params={"name": "coco-dataset", "persistent": true}
)

set_context(dataset_name="coco-dataset")

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

launch_app(dataset_name="coco-dataset")
```

## 2. YOLO dataset

```python
# Found: data.yaml, images/, labels/ (YOLOv5 format)

execute_operator(
    operator_uri="@voxel51/utils/create_dataset",
    params={"name": "yolo-dataset", "persistent": true}
)

set_context(dataset_name="yolo-dataset")

execute_operator(
    operator_uri="@voxel51/io/import_samples",
    params={
        "import_type": "MEDIA_AND_LABELS",
        "dataset_type": "YOLOv5",
        "dataset_dir": {"absolute_path": "/path/to/yolo/dataset"},
        "label_field": "ground_truth"
    }
)

launch_app(dataset_name="yolo-dataset")
```

## 3. Point cloud dataset

```python
# Found: 1000 .pcd files, labels/ with KITTI format

execute_operator(
    operator_uri="@voxel51/utils/create_dataset",
    params={"name": "lidar-dataset", "persistent": true}
)

set_context(dataset_name="lidar-dataset")

execute_operator(
    operator_uri="@voxel51/io/import_samples",
    params={
        "import_type": "MEDIA_ONLY",
        "style": "GLOB_PATTERN",
        "glob_patt": {"absolute_path": "/path/to/data/*.pcd"}
    }
)

launch_app(dataset_name="lidar-dataset")
```

## 4. Autonomous driving, multimodal groups

Multiple cameras plus LiDAR per scene, so this goes through Python directly rather than an
operator call:

```python
import fiftyone as fo
from pathlib import Path

dataset = fo.Dataset("driving-dataset", persistent=True)
dataset.add_group_field("group", default="front_camera")

data_dir = Path("/path/to/driving_data")
samples = []

slice_mapping = {
    "front": "front_camera",
    "left": "left_camera",
    "right": "right_camera",
    "rear": "rear_camera",
    "lidar": "lidar",
    "radar": "radar",
}

for scene_dir in sorted(data_dir.iterdir()):
    if not scene_dir.is_dir():
        continue

    group = fo.Group()
    for file in scene_dir.iterdir():
        for key, slice_name in slice_mapping.items():
            if key in file.stem.lower():
                samples.append(fo.Sample(filepath=str(file), group=group.element(slice_name)))
                break

dataset.add_samples(samples)
dataset.save()

print(f"Created {len(dataset.distinct('group.id'))} groups")
print(f"Slices: {dataset.group_slices}")
print(f"Media types: {dataset.group_media_types}")

session = fo.launch_app(dataset)
```

## 5. Classification directory tree

```python
# Found: cats/, dogs/, birds/ folders with images inside

execute_operator(
    operator_uri="@voxel51/utils/create_dataset",
    params={"name": "classification-dataset", "persistent": true}
)

set_context(dataset_name="classification-dataset")

execute_operator(
    operator_uri="@voxel51/io/import_samples",
    params={
        "import_type": "MEDIA_AND_LABELS",
        "dataset_type": "Image Classification Directory Tree",
        "dataset_dir": {"absolute_path": "/path/to/classification"},
        "label_field": "ground_truth"
    }
)

launch_app(dataset_name="classification-dataset")
```

## 6. Mixed media, images and videos

```python
# Found: images/, videos/ folders

execute_operator(
    operator_uri="@voxel51/utils/create_dataset",
    params={"name": "mixed-media", "persistent": true}
)

set_context(dataset_name="mixed-media")

execute_operator(
    operator_uri="@voxel51/io/import_samples",
    params={
        "import_type": "MEDIA_ONLY",
        "style": "DIRECTORY",
        "directory": {"absolute_path": "/path/to/images"},
        "tags": ["image"]
    }
)

execute_operator(
    operator_uri="@voxel51/io/import_samples",
    params={
        "import_type": "MEDIA_ONLY",
        "style": "DIRECTORY",
        "directory": {"absolute_path": "/path/to/videos"},
        "tags": ["video"]
    }
)

launch_app(dataset_name="mixed-media")
```

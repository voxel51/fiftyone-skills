---
name: fiftyone-dataset-import
description: Universal dataset import for FiftyOne supporting all media types (images, videos, point clouds, 3D scenes), all label formats (COCO, YOLO, VOC, CVAT, KITTI, etc.), and multimodal grouped datasets. Use when users want to import any dataset regardless of format, automatically detect folder structure, handle autonomous driving data with multiple cameras and LiDAR, or create grouped datasets from multimodal data. Requires FiftyOne MCP server.
---

# Universal Dataset Import for FiftyOne

## Overview

Import any dataset into FiftyOne regardless of media type, label format, or folder structure. Automatically detects and handles:

- **All media types**: images, videos, point clouds, 3D scenes
- **All label formats**: COCO, YOLO, VOC, CVAT, KITTI, OpenLABEL, and more
- **Multimodal groups**: Multiple cameras + LiDAR per scene (autonomous driving, robotics)
- **Complex folder structures**: Nested directories, scene-based organization

**Use this skill when:**
- Importing datasets from any source or format
- Working with autonomous driving data (multiple cameras, LiDAR, radar)
- Loading multimodal data that needs grouping
- The user doesn't know or specify the exact format
- Importing point clouds, 3D scenes, or mixed media types

## Prerequisites

- FiftyOne MCP server installed and running
- `@voxel51/io` plugin for importing data
- `@voxel51/utils` plugin for dataset management

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

### 4. Confirm before importing
Present findings to user and **explicitly ask for confirmation** before creating the dataset.
Always end your scan summary with a clear question like:
- "Proceed with import?"
- "Should I create the dataset with these settings?"

**Wait for user response before proceeding.** Do not create the dataset until the user confirms.

### 5. Check for existing datasets
Before creating a dataset, check if the proposed name already exists:
```python
list_datasets()
```
If the dataset name exists, ask the user:
- **Overwrite**: Delete existing and create new
- **Rename**: Use a different name (suggest alternatives like `dataset-name-v2`)
- **Abort**: Cancel the import

### 6. Validate after import
Compare imported sample count with source file count. Report any discrepancies.

### 7. Report errors minimally to user
Keep error messages simple for the user. Use detailed error info internally to diagnose issues.

## Complete Workflow

### Step 1: Deep Folder Scan

Scan the target directory to understand its structure:

```bash
# Count files by extension
find /path/to/data -type f | sed 's/.*\.//' | sort | uniq -c | sort -rn

# List directory structure (2 levels deep)
find /path/to/data -maxdepth 2 -type d

# Sample some files
ls -la /path/to/data/* | head -20
```

Build an inventory of:
- Media files by type (images, videos, point clouds, 3D)
- Label files by format (JSON, XML, TXT, YAML)
- Directory structure (flat vs nested vs scene-based)

### Step 2: Identify Media Types

Classify files by extension:

| Extensions | Media Type | FiftyOne Type |
|------------|------------|---------------|
| `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.webp`, `.tiff` | Image | `image` |
| `.mp4`, `.avi`, `.mov`, `.mkv`, `.webm` | Video | `video` |
| `.pcd`, `.ply`, `.las`, `.laz` | Point Cloud | `point-cloud` |
| `.fo3d`, `.obj`, `.gltf`, `.glb` | 3D Scene | `3d` |

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

### Step 4: Detect Grouping Pattern

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

### Step 5: Present Findings to User

Before importing, present a clear summary:

```
Scan Results for /path/to/data:

Media Found:
  - 3,000 images (.jpg, .png)
  - 1,000 point clouds (.pcd)
  - 0 videos

Grouping Detected:
  - Pattern: Scene folders
  - Groups: 1,000 scenes
  - Slices: left (image), right (image), front (image), lidar (point-cloud)

Labels Detected:
  - Format: COCO Detection
  - File: annotations/instances.json
  - Classes: 10 (car, pedestrian, cyclist, ...)

Proposed Configuration:
  - Dataset name: my-dataset
  - Type: Grouped (multimodal)
  - Default slice: front
  - Label field: ground_truth

Proceed with import? (yes/no)
```

**IMPORTANT:** Wait for user confirmation before proceeding to the next step. Do not create the dataset until the user explicitly confirms.

### Step 6: Check for Existing Dataset

Before creating, check if the dataset name already exists:

```python
# Check existing datasets
list_datasets()
```

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

### Step 7: Create Dataset

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

### Step 8A: Import Simple Dataset (No Groups)

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

### Step 8B: Import Grouped Dataset (Multimodal)

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

### Step 9: Import Labels for Grouped Dataset

After creating the grouped dataset, import labels:

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

### Step 10: Validate Import

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

### Step 11: Launch App and View

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

## Common Use Cases

### Use Case 1: Simple Image Dataset with COCO Labels

```python
# Scan directory
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

### Use Case 2: YOLO Dataset

```python
# Scan directory
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

### Use Case 3: Point Cloud Dataset

```python
# Scan directory
# Found: 1000 .pcd files, labels/ with KITTI format

execute_operator(
    operator_uri="@voxel51/utils/create_dataset",
    params={"name": "lidar-dataset", "persistent": true}
)

set_context(dataset_name="lidar-dataset")

# Import point clouds
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

### Use Case 4: Autonomous Driving (Multimodal Groups)

This is the most complex case - multiple cameras + LiDAR per scene:

```python
import fiftyone as fo
from pathlib import Path

# Create dataset with group support
dataset = fo.Dataset("driving-dataset", persistent=True)
dataset.add_group_field("group", default="front_camera")

data_dir = Path("/path/to/driving_data")
samples = []

# Process each scene folder
for scene_dir in sorted(data_dir.iterdir()):
    if not scene_dir.is_dir():
        continue

    group = fo.Group()

    # Map files to slices
    slice_mapping = {
        "front": "front_camera",
        "left": "left_camera",
        "right": "right_camera",
        "rear": "rear_camera",
        "lidar": "lidar",
        "radar": "radar"
    }

    for file in scene_dir.iterdir():
        # Determine slice from filename
        for key, slice_name in slice_mapping.items():
            if key in file.stem.lower():
                samples.append(fo.Sample(
                    filepath=str(file),
                    group=group.element(slice_name)
                ))
                break

dataset.add_samples(samples)
dataset.save()

print(f"Created {len(dataset.distinct('group.id'))} groups")
print(f"Slices: {dataset.group_slices}")
print(f"Media types: {dataset.group_media_types}")

# Launch app
session = fo.launch_app(dataset)
```

### Use Case 5: Classification Directory Tree

```python
# Scan directory
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

### Use Case 6: Mixed Media (Images + Videos)

```python
# Scan directory
# Found: images/, videos/ folders

# Create dataset
execute_operator(
    operator_uri="@voxel51/utils/create_dataset",
    params={"name": "mixed-media", "persistent": true}
)

set_context(dataset_name="mixed-media")

# Import images
execute_operator(
    operator_uri="@voxel51/io/import_samples",
    params={
        "import_type": "MEDIA_ONLY",
        "style": "DIRECTORY",
        "directory": {"absolute_path": "/path/to/images"},
        "tags": ["image"]
    }
)

# Import videos
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

**Groups not detected**
- Check folder structure matches expected patterns
- Verify consistent naming across scenes
- May need to specify grouping manually

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
- [Supported Dataset Formats](https://docs.voxel51.com/user_guide/dataset_creation/datasets.html)
- [FiftyOne I/O Plugin](https://github.com/voxel51/fiftyone-plugins/tree/main/plugins/io)

## License

Copyright 2017-2025, Voxel51, Inc.
Apache 2.0 License

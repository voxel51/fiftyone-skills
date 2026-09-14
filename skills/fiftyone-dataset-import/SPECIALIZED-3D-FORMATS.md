# Specialized 3D and autonomous driving formats

Read this when a scan turns up a named autonomous-driving devkit format (PandaSet, nuScenes, Waymo
Open, Argoverse, KITTI 3D, Lyft L5, A2D2) rather than a plain point-cloud or image directory. These
formats need an external devkit to parse, plus a conversion step into FiftyOne's own 3D
representation. For MCAP robotics/AV recordings specifically, see
[MCAP-AUTHORING.md](MCAP-AUTHORING.md), [MCAP-TROUBLESHOOTING.md](MCAP-TROUBLESHOOTING.md), and
[MCAP-DATASET-AND-VALIDATION.md](MCAP-DATASET-AND-VALIDATION.md) instead.

## Contents

1. [Directory pattern detection](#directory-pattern-detection)
2. [Required packages](#required-packages)
3. [Converting point clouds to PCD](#converting-point-clouds-to-pcd)
4. [Creating fo.Scene for 3D visualization](#creating-foscene-for-3d-visualization)
5. [Mapping labels to FiftyOne types](#mapping-labels-to-fiftyone-types)
6. [Complete example: PandaSet with all labels](#complete-example-pandaset-with-all-labels)
7. [No example exists for this format](#no-example-exists-for-this-format)

## Directory pattern detection

| Directory pattern | Format | Required package |
|---|---|---|
| `camera/`, `lidar/`, `annotations/cuboids/` with `.pkl.gz` | PandaSet | `pandaset-devkit` |
| `samples/`, `sweeps/`, `v1.0-*` folders | nuScenes | `nuscenes-devkit` |
| `segment-*` with `.tfrecord` files | Waymo Open | `waymo-open-dataset-tf` |
| `argoverse-tracking/` structure | Argoverse | `argoverse-api` |
| `training/`, `testing/` with `calib/`, `velodyne/` | KITTI 3D | `pykitti` |
| `scenes/`, `aerial_map/` | Lyft L5 | `l5kit` |

## Required packages

| Format | Package | Install |
|---|---|---|
| PandaSet | `pandaset` | `pip install "git+https://github.com/scaleapi/pandaset-devkit.git#subdirectory=python"` |
| nuScenes | `nuscenes-devkit` | `pip install nuscenes-devkit` |
| Waymo Open | `waymo-open-dataset-tf` | See Waymo docs (requires TensorFlow) |
| Argoverse 2 | `av2` | `pip install av2` |
| KITTI 3D | `pykitti` | `pip install pykitti` |
| Lyft L5 | `l5kit` | `pip install l5kit` |
| A2D2 | `a2d2` | See Audi A2D2 docs |

Check whether the package is already installed (`pip show <package>`), then ask the user for
permission before installing. If the package isn't on PyPI, install from GitHub, with a
subdirectory flag for monorepos (`pip install "git+https://github.com/<org>/<repo>.git#subdirectory=python"`).
After installing, verify with `pip show <package>` and a smoke-test import.

If the format isn't in the table above, search PyPI and GitHub for `<format-name>-devkit` or
`<format-name>-sdk`, check the dataset's official site for developer tools, and search "FiftyOne
import `<format-name>`" before writing custom code.

## Converting point clouds to PCD

Autonomous driving datasets store LiDAR data in proprietary formats (`.pkl.gz`, `.bin`, `.npy`).
FiftyOne requires `.pcd` files, so convert first (`pip install open3d` if needed):

```python
import numpy as np
import open3d as o3d
from pathlib import Path

def convert_to_pcd(points, output_path):
    """points: (N, 3) or (N, 4) array with XYZ or XYZI. Writes a .pcd file."""
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points[:, :3])

    if points.shape[1] >= 4:
        intensity = points[:, 3]
        intensity_normalized = (intensity - intensity.min()) / (intensity.max() - intensity.min() + 1e-8)
        colors = np.stack([intensity_normalized] * 3, axis=1)
        pcd.colors = o3d.utility.Vector3dVector(colors)

    o3d.io.write_point_cloud(str(output_path), pcd)
    return output_path
```

## Creating fo.Scene for 3D visualization

For each LiDAR frame, create an `fo.Scene` that references the PCD file:

```python
import fiftyone as fo

scene = fo.Scene()
scene.add_point_cloud(
    name="lidar",
    pcd_path="/path/to/frame.pcd",
    flag_for_projection=True,  # enables projection to camera views
)

sample = fo.Sample(filepath="/path/to/scene.fo3d")
sample["scene"] = scene
```

## Mapping labels to FiftyOne types

| Annotation type | FiftyOne label type | Field name |
|---|---|---|
| 3D cuboids/bounding boxes | `fo.Detection` with 3D attributes | `detections_3d` |
| Semantic segmentation | `fo.Segmentation` | `segmentation` |
| Instance segmentation | `fo.Detections` with masks | `instances` |
| Tracking IDs | `track_id` added to detections | `tracks` |
| Classification | `fo.Classification` | `classification` |
| Keypoints/pose | `fo.Keypoints` | `keypoints` |

## Complete example: PandaSet with all labels

```python
import fiftyone as fo
import numpy as np
import open3d as o3d
from pathlib import Path
import gzip
import pickle

data_path = Path("/path/to/pandaset")
pcd_output_dir = data_path / "pcd_converted"
pcd_output_dir.mkdir(exist_ok=True)

dataset = fo.Dataset("pandaset", persistent=True)
dataset.add_group_field("group", default="front_camera")

camera_names = [d.name for d in (data_path / "camera").iterdir() if d.is_dir()]
frame_count = len(list((data_path / "camera" / "front_camera").glob("*.jpg")))

labels_dir = data_path / "annotations"
available_labels = [d.name for d in labels_dir.iterdir() if d.is_dir()]
print(f"Found label types: {available_labels}")  # e.g., ['cuboids', 'semseg']

samples = []
for frame_idx in range(frame_count):
    frame_id = f"{frame_idx:02d}"
    group = fo.Group()

    for cam_name in camera_names:
        img_path = data_path / "camera" / cam_name / f"{frame_id}.jpg"
        if img_path.exists():
            sample = fo.Sample(filepath=str(img_path))
            sample["group"] = group.element(cam_name)
            sample["frame_idx"] = frame_idx
            samples.append(sample)

    lidar_pkl = data_path / "lidar" / f"{frame_id}.pkl.gz"
    if lidar_pkl.exists():
        with gzip.open(lidar_pkl, "rb") as f:
            lidar_data = pickle.load(f)

        points = lidar_data.get("points", lidar_data.get("data")) if isinstance(lidar_data, dict) \
            else np.array(lidar_data)

        pcd_path = pcd_output_dir / f"{frame_id}.pcd"
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(points[:, :3])
        o3d.io.write_point_cloud(str(pcd_path), pcd)

        lidar_sample = fo.Sample(filepath=str(pcd_path))
        lidar_sample["group"] = group.element("lidar")
        lidar_sample["frame_idx"] = frame_idx

        # Store 3D attributes as flat scalar fields, not lists. A list (e.g.
        # location=[x, y, z]) causes "Symbol.iterator" errors in the 3D viewer.
        if "cuboids" in available_labels:
            cuboids_pkl = labels_dir / "cuboids" / f"{frame_id}.pkl.gz"
            if cuboids_pkl.exists():
                with gzip.open(cuboids_pkl, "rb") as f:
                    cuboids_df = pickle.load(f)  # PandaSet uses a pandas DataFrame

                detections = []
                for _, row in cuboids_df.iterrows():
                    detection = fo.Detection(
                        label=row.get("label", "object"),
                        bounding_box=[0, 0, 0.01, 0.01],  # minimal 2D placeholder
                    )
                    detection["pos_x"] = float(row.get("position.x", 0))
                    detection["pos_y"] = float(row.get("position.y", 0))
                    detection["pos_z"] = float(row.get("position.z", 0))
                    detection["dim_x"] = float(row.get("dimensions.x", 1))
                    detection["dim_y"] = float(row.get("dimensions.y", 1))
                    detection["dim_z"] = float(row.get("dimensions.z", 1))
                    detection["yaw"] = float(row.get("yaw", 0))
                    detection["track_id"] = str(row.get("uuid", ""))
                    detection["stationary"] = bool(row.get("stationary", False))
                    detections.append(detection)

                lidar_sample["ground_truth"] = fo.Detections(detections=detections)

        if "semseg" in available_labels:
            semseg_pkl = labels_dir / "semseg" / f"{frame_id}.pkl.gz"
            if semseg_pkl.exists():
                with gzip.open(semseg_pkl, "rb") as f:
                    semseg_data = pickle.load(f)
                lidar_sample["point_labels"] = semseg_data.tolist() if hasattr(semseg_data, "tolist") else semseg_data

        samples.append(lidar_sample)

dataset.add_samples(samples)
dataset.save()

print(f"Imported {len(dataset)} groups with {len(dataset.select_group_slices())} total samples")
print(f"Slices: {dataset.group_slices}")
print(f"Labels imported: {available_labels}")
```

## No example exists for this format

1. Search "FiftyOne `<format-name>` import example" and "`<format-name>` devkit python example".
2. Read the devkit documentation to understand the data structure.
3. Explore an annotation file directly:
   ```python
   import pickle, gzip
   with gzip.open("annotations/cuboids/00.pkl.gz", "rb") as f:
       data = pickle.load(f)
   print(type(data), data[0] if isinstance(data, list) else data)
   ```
4. Build custom import code from the devkit API and the label structure you found.

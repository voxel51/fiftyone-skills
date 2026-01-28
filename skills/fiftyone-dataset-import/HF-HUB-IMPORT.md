# Importing from Hugging Face Hub

Import datasets directly from Hugging Face Hub into FiftyOne. Supports FiftyOne-formatted datasets, generic parquet datasets, and standard ML formats (COCO, YOLO, etc.) stored on HF.

## Authentication Setup

Configure authentication using one of these methods:

**Option 1: Environment Variable (Recommended)**
```bash
export HF_TOKEN="hf_your_token_here"
```

**Option 2: Hugging Face CLI**
```bash
pip install huggingface_hub
huggingface-cli login
```

Verify authentication:
```python
from huggingface_hub import whoami
print(whoami())  # Shows your username if authenticated
```

## Detecting HF Sources

Recognize Hugging Face dataset references in these formats:
- Full URL: `https://huggingface.co/datasets/username/dataset-name`
- Short form: `username/dataset-name`
- HF protocol: `hf://datasets/username/dataset-name`

## Scan HF Repository First

**ALWAYS scan the HF repository before importing** to understand its structure:

```python
from huggingface_hub import list_repo_files, hf_hub_download

repo_id = "username/dataset-name"

# List all files in repository
files = list_repo_files(repo_id, repo_type="dataset")
print("Files:", files[:20])

# Check for fiftyone.yml
has_fiftyone = "fiftyone.yml" in files
print(f"FiftyOne-formatted: {has_fiftyone}")

# Check for parquet files
parquet_files = [f for f in files if f.endswith('.parquet')]
print(f"Parquet files: {len(parquet_files)}")

# For parquet datasets, inspect schema
if parquet_files:
    # Download README to check schema documentation
    readme = hf_hub_download(repo_id, "README.md", repo_type="dataset")
    with open(readme) as f:
        content = f.read()
    # Look for "features:" or column names in README
```

## Present Import Options to User

After scanning, **ALWAYS present options and ask user what to import** before proceeding.

**Key directive:** NEVER assume what to import. Different users need different things from the same dataset.

**Template for presenting options:**

```
Scan complete for [repo_id]

Available data:
├── Media: [type, resolution, count]
├── Labels: [field names, types]
├── Metadata: [additional fields]
└── Format: [fiftyone.yml | parquet | COCO/YOLO | custom]

Import options:
1. [Recommended option] (recommended)
2. [Alternative option]
3. [Subset/limited option]
4. Custom selection

Which would you like to import?
```

**Format-specific prompts:**

For **parquet datasets**:
```
Import options:
1. Images + labels (recommended)
2. Images only
3. Subset (specify split or max_samples)
```

For **video/temporal datasets**:
```
Import options:
1. Video files (recommended) - preserves temporal continuity
2. Individual frames - extract as images
3. Video + metadata as frame-level fields
```

For **multi-format datasets** (has both COCO and YOLO):
```
Import options:
1. COCO format (recommended)
2. YOLO format
3. Raw images only
```

**Wait for user response before importing.**

## Import Strategy (Auto-Detection)

When importing from HF Hub, follow this decision tree:

1. **Check for `fiftyone.yml`** → Use `load_from_hub()` directly
2. **Parquet-based dataset?** → Try `load_from_hub(format="ParquetFilesDataset")`
   - If rate limited → Use fallback: `snapshot_download()` + parquet extraction (Step 4)
3. **Other formats (COCO, YOLO, VOC)** → Download with `snapshot_download()`, then import locally

**IMPORTANT:** Large parquet datasets (>10K samples) may hit HF API rate limits. If `load_from_hub()` fails with JSON decode errors or timeouts, use the parquet extraction fallback in Step 4.

## Step 1: FiftyOne-Formatted Datasets

For datasets with `fiftyone.yml` (tagged with `library:fiftyone` on HF):

```python
import fiftyone as fo
from fiftyone.utils.huggingface import load_from_hub

# Basic import
dataset = load_from_hub("username/dataset-name")

# With options
dataset = load_from_hub(
    "username/dataset-name",
    name="my-local-name",        # Custom dataset name
    persistent=True,             # Save to database
    max_samples=1000,            # Limit samples
    split="train",               # Specific split
    overwrite=True,              # Overwrite if exists
)

# Launch app to view
session = fo.launch_app(dataset)
```

**List available FiftyOne datasets on HF:**
```python
from fiftyone.utils.huggingface import list_hub_datasets

# Get dataset names
datasets = list_hub_datasets()
print(datasets)  # ['voxel51/VisDrone2019-DET', 'user/dataset', ...]

# Get detailed info
datasets_info = list_hub_datasets(info=True)
for ds in datasets_info:
    print(f"{ds.id}: {ds.downloads} downloads")
```

## Step 2: Generic Parquet-Based Datasets

Most HF datasets store data as parquet files. Use `format="ParquetFilesDataset"` with field mappings:

```python
from fiftyone.utils.huggingface import load_from_hub

# Image classification dataset (e.g., CIFAR, ImageNet subsets)
dataset = load_from_hub(
    "username/image-classification-dataset",
    format="ParquetFilesDataset",
    filepath="image",                    # Column containing images
    classification_fields="label",       # Column for labels
    name="my-classification-dataset",
    persistent=True,
    max_samples=5000,
)

# Object detection dataset
dataset = load_from_hub(
    "username/detection-dataset",
    format="ParquetFilesDataset",
    filepath="image",
    detection_fields="objects",          # Column for detections
    name="my-detection-dataset",
    persistent=True,
)

# With specific split and subset
dataset = load_from_hub(
    "username/multi-config-dataset",
    format="ParquetFilesDataset",
    filepath="image",
    split="train",
    subset="config_name",                # Dataset config/subset
    persistent=True,
)
```

**Common field mappings:**

| HF Column Type | FiftyOne Parameter | Example |
|----------------|-------------------|---------|
| Image column | `filepath="image"` | Most image datasets |
| Class label | `classification_fields="label"` | CIFAR, ImageNet |
| Bounding boxes | `detection_fields="objects"` | COCO-style |
| Segmentation mask | `mask_fields="segmentation"` | Semantic seg |
| Thumbnail | `thumbnail_path="thumbnail"` | Datasets with previews |

## Step 3: Other Formats (COCO, YOLO, etc. on HF)

For datasets storing raw COCO/YOLO/VOC files on HF (not parquet), download first:

```python
import fiftyone as fo
from huggingface_hub import snapshot_download

# Download the repository
local_path = snapshot_download(
    repo_id="username/coco-style-dataset",
    repo_type="dataset",
    local_dir="/path/to/download",
)

# Now scan and import using standard methods
# (Follow the local import workflow from SKILL.md)

# Example: COCO format detected
dataset = fo.Dataset.from_dir(
    dataset_dir=local_path,
    dataset_type=fo.types.COCODetectionDataset,
    name="hf-coco-dataset",
)
```

**Workflow for unknown HF formats:**

1. **Download and scan:**
```python
from huggingface_hub import snapshot_download

local_path = snapshot_download(
    repo_id="username/dataset-name",
    repo_type="dataset",
)
```

2. **Explore structure:**
```bash
find /path/to/download -type f | head -50
ls -la /path/to/download
```

3. **Detect format** using patterns from "Detect Label Format" section in SKILL.md

4. **Import** using appropriate dataset type

## Step 4: Parquet Extraction Fallback (Rate Limit Recovery)

When `load_from_hub(format="ParquetFilesDataset")` fails due to HF API rate limits, extract images manually from downloaded parquet files.

**When to use this fallback:**
- `JSONDecodeError` during parquet streaming
- Timeout errors on large datasets (>10K samples)
- Connection reset errors

**Complete workflow:**

```python
import fiftyone as fo
import pyarrow.parquet as pq
from pathlib import Path
from PIL import Image
from huggingface_hub import snapshot_download
import io

# Step 1: Download parquet files
local_path = snapshot_download(
    repo_id="username/dataset-name",
    repo_type="dataset",
    local_dir="/tmp/hf-download",
)

# Step 2: Find and read parquet file
parquet_files = list(Path(local_path).rglob("*.parquet"))
table = pq.read_table(parquet_files[0])
df = table.to_pandas()

# Step 3: Inspect schema to find image and label columns
print(f"Columns: {list(df.columns)}")
print(f"Sample row: {df.iloc[0]}")

# Step 4: Extract images and create samples
output_dir = Path("/tmp/extracted-images")
output_dir.mkdir(exist_ok=True)

samples = []
for idx, row in df.iterrows():
    # Extract image from bytes (common HF format)
    img_data = row['image']  # Adjust column name as needed
    if isinstance(img_data, dict) and 'bytes' in img_data:
        img_bytes = img_data['bytes']
    else:
        img_bytes = img_data

    # Save image
    img = Image.open(io.BytesIO(img_bytes))
    img_path = output_dir / f"{idx:06d}.png"
    img.save(img_path)

    # Create FiftyOne sample with label
    sample = fo.Sample(filepath=str(img_path))

    # Add classification label (adjust field name as needed)
    if 'label' in row:
        sample["ground_truth"] = fo.Classification(label=str(row['label']))

    samples.append(sample)

# Step 5: Create dataset
dataset = fo.Dataset("extracted-dataset", persistent=True)
dataset.add_samples(samples)

print(f"Imported {len(dataset)} samples")
```

**Adapting for different schemas:**

| HF Column Structure | Extraction Code |
|---------------------|-----------------|
| `{'bytes': b'...', 'path': '...'}` | `img_data['bytes']` |
| Raw bytes | `img_data` directly |
| Base64 string | `base64.b64decode(img_data)` |
| File path reference | Download separately |

## Complete HF Import Examples

**Example 1: FiftyOne Dataset from HF**
```python
import fiftyone as fo
from fiftyone.utils.huggingface import load_from_hub

# Load FiftyOne-formatted dataset
dataset = load_from_hub(
    "Voxel51/VisDrone2019-DET",
    persistent=True,
    max_samples=500,
)

print(f"Loaded {len(dataset)} samples")
print(f"Fields: {dataset.get_field_schema().keys()}")

session = fo.launch_app(dataset)
```

**Example 2: Generic HF Image Dataset**
```python
from fiftyone.utils.huggingface import load_from_hub

# Load parquet-based image classification dataset
dataset = load_from_hub(
    "cifar10",                           # Short name works
    format="ParquetFilesDataset",
    filepath="img",                      # CIFAR uses "img" column
    classification_fields="label",
    split="train",
    max_samples=1000,
    name="cifar10-sample",
    persistent=True,
)
```

**Example 3: Download and Import COCO from HF**
```python
import fiftyone as fo
from huggingface_hub import snapshot_download

# Download COCO-format dataset from HF
local_path = snapshot_download(
    repo_id="detection-datasets/coco",
    repo_type="dataset",
    local_dir="./hf_coco_download",
)

# Import as COCO
dataset = fo.Dataset.from_dir(
    dataset_dir=local_path,
    dataset_type=fo.types.COCODetectionDataset,
    name="hf-coco",
    persistent=True,
)

session = fo.launch_app(dataset)
```

**Example 4: Parquet Extraction Fallback (MNIST-style)**
```python
import fiftyone as fo
import pyarrow.parquet as pq
from pathlib import Path
from PIL import Image
from huggingface_hub import snapshot_download
import io

# Download MNIST dataset
local_path = snapshot_download(
    repo_id="ylecun/mnist",
    repo_type="dataset",
    local_dir="/tmp/mnist-download",
)

# Read parquet
parquet_path = Path(local_path) / "mnist" / "train-00000-of-00001.parquet"
df = pq.read_table(parquet_path).to_pandas()

# Extract images
output_dir = Path("/tmp/mnist-images")
output_dir.mkdir(exist_ok=True)

samples = []
for idx, row in df.iterrows():
    # MNIST stores images as {'bytes': b'...', 'path': '...'}
    img = Image.open(io.BytesIO(row['image']['bytes']))
    img_path = output_dir / f"{idx:05d}.png"
    img.save(img_path)

    sample = fo.Sample(filepath=str(img_path))
    sample["ground_truth"] = fo.Classification(label=str(row['label']))
    samples.append(sample)

# Create dataset
dataset = fo.Dataset("mnist", persistent=True)
dataset.add_samples(samples)
```

## HF Import Troubleshooting

**Error: "JSONDecodeError" or "Expecting value" during parquet import**
- HF API rate limit hit (common with datasets >10K samples)
- Solution: Use parquet extraction fallback (Step 4)
- Install pyarrow: `pip install pyarrow`

**Error: "Could not find fiftyone metadata"**
- Dataset lacks `fiftyone.yml` config
- Solution: Use `format="ParquetFilesDataset"` with field mappings, or download and import locally

**Error: "401 Unauthorized"**
- Token missing or invalid
- Solution: Set `HF_TOKEN` env var or run `huggingface-cli login`

**Error: "Repository not found"**
- Private repo without token, or typo in repo_id
- Solution: Verify repo exists at `huggingface.co/datasets/{repo_id}`, ensure token has read access

**Error: "Invalid filepath column"**
- Wrong column name for media field
- Solution: Check dataset schema on HF website, use correct column name in `filepath` parameter

**Error: "Unable to find a usable engine" for parquet**
- Missing pyarrow or fastparquet
- Solution: `pip install pyarrow`

**Slow download for large datasets**
- Use `max_samples` to limit initial import
- Use `split` to load only needed splits
- Consider streaming with parquet format

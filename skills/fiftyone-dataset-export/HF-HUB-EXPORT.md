# Exporting to Hugging Face Hub

Push FiftyOne datasets directly to Hugging Face Hub for sharing, backup, or collaboration.

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

**Verify authentication and check username:**
```python
from huggingface_hub import whoami
user_info = whoami()
print(f"Logged in as: {user_info['name']}")
```

## Dataset Card Workflow

**ALWAYS generate a dataset card and present to user for approval before uploading.**

1. Analyze dataset: `len(dataset)`, `media_type`, `get_field_schema()`, `distinct('tags')`
2. Generate README.md using template below
3. Present card to user for approval
4. Upload after approval

**Card template:**
```markdown
---
license: apache-2.0
task_categories:
  - [detected-task-type]
tags:
  - fiftyone
  - computer-vision
---

# [Dataset Name]

[Description from analysis]

## Details

| Property | Value |
|----------|-------|
| Samples | [count] |
| Media | [type] |
| Fields | [key fields] |

## Usage

\`\`\`python
from fiftyone.utils.huggingface import load_from_hub
dataset = load_from_hub("[repo-id]")
\`\`\`

---
*Uploaded with [FiftyOne Skills](https://github.com/voxel51/fiftyone-skills)*
```

## Push to Hub Workflow

Use `push_to_hub()` for personal accounts. Handles:
- Repository creation
- FiftyOne format export
- `fiftyone.yml` config
- Auto-chunking (>10K samples)

**Basic usage:**
```python
import fiftyone as fo
from fiftyone.utils.huggingface import push_to_hub

# Load your dataset
dataset = fo.load_dataset("my-dataset")

# Push to Hub (creates repo: your-username/my-hf-dataset)
push_to_hub(
    dataset,
    repo_name="my-hf-dataset",
)
```

**With all options:**
```python
push_to_hub(
    dataset,
    repo_name="my-hf-dataset",
    description="A curated dataset for object detection",
    license="mit",
    tags=["object-detection", "autonomous-driving", "custom-tag"],
    private=True,                    # Private repository
    exist_ok=True,                   # Don't error if repo exists
    preview_path="/path/to/preview.jpg",  # Preview image for README
    min_fiftyone_version="0.23.0",   # Minimum FiftyOne version required
    label_field="ground_truth",      # Specific label field(s) to export
    token="hf_...",                  # Override HF_TOKEN env var
)
```

## Parameters Reference

| Parameter | Type | Description |
|-----------|------|-------------|
| `dataset` | Dataset | FiftyOne dataset to push |
| `repo_name` | str | Repository name (creates `{username}/{repo_name}`). For organizations, see Use Case 6 |
| `description` | str | Dataset description for the card |
| `license` | str | License identifier (e.g., "mit", "apache-2.0", "cc-by-4.0") |
| `tags` | list | Additional tags (auto-includes "fiftyone", media type, task type) |
| `private` | bool | Whether repo should be private (default: False) |
| `exist_ok` | bool | Don't error if repo already exists (default: False) |
| `preview_path` | str | Path to preview image/video for README |
| `min_fiftyone_version` | str | Minimum FiftyOne version to load dataset |
| `label_field` | str/list | Label field(s) to export (default: all) |
| `frame_labels_field` | str/list | Frame label field(s) for video datasets |
| `token` | str | HF token (overrides HF_TOKEN env var) |
| `chunk_size` | int | Files per subdirectory (auto: 1000 for >10K samples) |

## Use Cases

**Use Case 1: Share Public Dataset**
```python
import fiftyone as fo
from fiftyone.utils.huggingface import push_to_hub
from huggingface_hub import HfApi

dataset = fo.load_dataset("my-annotated-dataset")

push_to_hub(
    dataset,
    repo_name="street-signs-detection",
    description="Street sign detection dataset with 5000 annotated images",
    license="cc-by-4.0",
    tags=["object-detection", "traffic-signs", "autonomous-driving"],
    preview_path="./sample_image.jpg",
)

# Upload approved README (from Dataset Card Workflow above)
api = HfApi()
api.upload_file(
    path_or_fileobj=readme_content.encode(),
    path_in_repo="README.md",
    repo_id="your-username/street-signs-detection",
    repo_type="dataset",
    commit_message="Update dataset card",
)
```

**Use Case 2: Private Backup**
```python
from huggingface_hub import HfApi

push_to_hub(
    dataset,
    repo_name="project-backup-2024",
    private=True,
    description="Internal project backup with all annotations and brain runs",
)

# Upload approved README
api = HfApi()
api.upload_file(
    path_or_fileobj=readme_content.encode(),
    path_in_repo="README.md",
    repo_id="your-username/project-backup-2024",
    repo_type="dataset",
    commit_message="Update dataset card",
)
```

**Use Case 3: Export Filtered View**
```python
import fiftyone as fo
from fiftyone.utils.huggingface import push_to_hub

dataset = fo.load_dataset("large-dataset")

# Create a filtered view
validated_view = dataset.match_tags("validated").limit(1000)

# Convert view to dataset for export
validated_dataset = validated_view.clone("validated-subset")

push_to_hub(
    validated_dataset,
    repo_name="validated-subset",
    description="Curated subset of validated samples",
    tags=["curated", "high-quality"],
)
```

**Use Case 4: Export Specific Labels**
```python
push_to_hub(
    dataset,
    repo_name="detection-only-dataset",
    label_field="detections",           # Only export detections field
    description="Dataset with detection annotations only",
)

# Or multiple fields
push_to_hub(
    dataset,
    repo_name="multi-label-dataset",
    label_field=["detections", "classifications"],
)
```

**Use Case 5: Video Dataset with Frame Labels**
```python
push_to_hub(
    video_dataset,
    repo_name="video-tracking-dataset",
    label_field="detections",
    frame_labels_field="frames.detections",  # Frame-level annotations
    description="Video dataset with per-frame tracking annotations",
)
```

**Use Case 6: Push to Organization (or Private Org Repo)**

`push_to_hub()` only supports personal accounts. For organizations or private organization repos, use manual upload:

```python
import fiftyone as fo
from huggingface_hub import HfApi, create_repo

dataset = fo.load_dataset("my-dataset")

# Export locally
export_dir = "/tmp/my-dataset-export"
dataset.export(export_dir=export_dir, dataset_type=fo.types.FiftyOneDataset)

# Create org repo (set private=True for private repos)
repo_id = "OrgName/my-dataset"
create_repo(repo_id, repo_type="dataset", exist_ok=True, private=False)

# Upload dataset files
api = HfApi()
api.upload_folder(
    folder_path=export_dir,
    repo_id=repo_id,
    repo_type="dataset",
    commit_message="Upload dataset",
)

# Create fiftyone.yml config (required for load_from_hub)
fiftyone_config = f"""name: {dataset.name}
format: FiftyOneDataset
"""
api.upload_file(
    path_or_fileobj=fiftyone_config.encode(),
    path_in_repo="fiftyone.yml",
    repo_id=repo_id,
    repo_type="dataset",
    commit_message="Add fiftyone.yml config",
)

# Upload approved README (from Dataset Card Workflow above)
api.upload_file(
    path_or_fileobj=readme_content.encode(),
    path_in_repo="README.md",
    repo_id=repo_id,
    repo_type="dataset",
    commit_message="Add dataset card",
)
```

## What Gets Uploaded

When you push to Hub, FiftyOne uploads:
- **Media files** (images, videos, point clouds)
- **Sample metadata** (all fields, tags, custom attributes)
- **Labels** (detections, classifications, segmentations, etc.)
- **Brain runs** (embeddings, similarity indexes, etc.)
- **Evaluations** (model evaluation results)
- **Dataset config** (`fiftyone.yml` for loading)
- **Dataset card** (README with usage instructions)

## HF Export Troubleshooting

**Error: "401 Unauthorized" or "Invalid token"**
- Token missing, expired, or lacks write permissions
- Solution: Create new token at huggingface.co/settings/tokens with "Write" scope

**Error: "Repository already exists"**
- Repo with same name exists under your account
- Solution: Use `exist_ok=True` to update existing, or choose different name

**Error: "Permission denied for private repo"**
- Free HF account has limits on private repos
- Solution: Use public repo, or upgrade HF account

**Upload is slow for large datasets**
- Expected for large media files
- FiftyOne auto-chunks datasets >10K samples
- Consider exporting a view/subset first

**Missing brain runs or evaluations after load**
- Brain/evaluation data exports with the dataset
- Verify with `dataset.list_brain_runs()` before push

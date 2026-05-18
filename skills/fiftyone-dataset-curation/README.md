# Dataset Curation

End-to-end curation pipeline: inspect quality, audit annotations, find duplicates, explore embeddings, and build curated splits.

## Install

```bash
curl -sL skil.sh | sh -s -- voxel51/fiftyone-skills
```

When prompted, select **fiftyone-dataset-curation** from the menu.

## Requirements

- [FiftyOne](https://docs.voxel51.com/getting_started/install.html)
- [FiftyOne MCP Server](https://github.com/voxel51/fiftyone-mcp-server)

## Usage

Load a dataset in FiftyOne, then ask your AI assistant:

```
"Curate my dataset: check quality, find duplicates, and build a clean training split"
"Audit the annotations in my detection dataset"
"Analyze class distribution and flag imbalanced classes"
"Create a stratified train/val/test split"
```

The skill runs each phase sequentially and presents findings before making any changes.

## Example

```python
import fiftyone as fo
import fiftyone.zoo as foz

dataset = foz.load_zoo_dataset("quickstart")
```

Then ask your assistant:

```
"Curate the quickstart dataset: check for quality issues and near-duplicates"
```

## See also

- [Dataset curation docs](https://docs.voxel51.com/user_guide/brain.html)
- [FiftyOne Brain](https://github.com/voxel51/fiftyone-brain)

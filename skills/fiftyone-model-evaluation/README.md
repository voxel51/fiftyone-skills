# Model Evaluation

Evaluate model predictions against ground truth. Compute mAP, precision, recall, confusion matrices, and analyze failure cases.

## Install

```bash
curl -sL skil.sh | sh -s -- voxel51/fiftyone-skills
```

When prompted, select **fiftyone-model-evaluation** from the menu.

## Requirements

- [FiftyOne](https://docs.voxel51.com/getting_started/install.html)
- [FiftyOne MCP Server](https://github.com/voxel51/fiftyone-mcp-server) (optional, recommended for operator-based evaluation)
- `@voxel51/evaluation` plugin (optional, for operator-based evaluation)

## Usage

Load a dataset with both predictions and ground truth, then ask your AI assistant:

```
"Evaluate my YOLO predictions against ground truth"
"Compute mAP for my detection model"
"Show me the confusion matrix and top failure cases"
```

The skill checks for the required fields, runs the evaluation protocol, and opens the results in the App so you can drill into TP/FP/FN samples.

## Example


Then ask your assistant:

```
"Evaluate the predictions field against ground_truth in the quickstart dataset"
```

## See also

- [Model evaluation docs](https://docs.voxel51.com/user_guide/evaluation.html)

---
name: fiftyone-dataset-inference
description: Run ML model inference (YOLO, YOLOv8, CLIP, SAM, Detectron2, etc.) on FiftyOne datasets. Use when running models, applying detection, classification, segmentation, embeddings, or any model prediction task. Also use for end-to-end workflows that include importing data then running inference.
---

# Run Model Inference on FiftyOne Datasets

## Key Directives

**ALWAYS follow these rules:**

### 1. Check if dataset exists first
```python
list_datasets()
```
If the dataset doesn't exist, use the **fiftyone-dataset-import** skill to load it first.

### 2. Set context before operations
```python
set_context(dataset_name="my-dataset")
```

### 3. Launch App for inference
The App must be running to execute inference operators:
```python
launch_app(dataset_name="my-dataset")
```

### 4. Ask user for field names
Always confirm with the user:
- Which model to use
- Label field name for predictions (e.g., `predictions`, `detections`, `embeddings`)

### 5. Close app when done
```python
close_app()
```

## Workflow

### Step 1: Verify Dataset Exists

```python
list_datasets()
```

If the dataset is not in the list:
- Ask the user for the data location
- **Use the fiftyone-dataset-import skill** to import the data first
- Return to this workflow after import completes

### Step 2: Load Dataset and Review

```python
set_context(dataset_name="my-dataset")
dataset_summary(name="my-dataset")
```

Review:
- Sample count
- Media type
- Existing label fields

### Step 3: Launch App

```python
launch_app(dataset_name="my-dataset")
```

### Step 4: Apply Model Inference

Ask user for:
- Model name (see **Available Zoo Models** below)
- Label field for predictions

```python
execute_operator(
    operator_uri="@voxel51/zoo/apply_zoo_model",
    params={
        "tab": "BUILTIN",
        "model": "yolov8n-coco-torch",
        "label_field": "predictions"
    }
)
```

### Step 5: View Results

```python
set_view(exists=["predictions"])
```

### Step 6: Clean Up

```python
close_app()
```

## Available Zoo Models

Some models require additional packages. If a model fails with a dependency error, the response includes `install_command`. Offer to run it for the user.

### Detection Models

| Model | Description | Extra Deps |
|-------|-------------|------------|
| `faster-rcnn-resnet50-fpn-coco-torch` | Faster R-CNN | None |
| `retinanet-resnet50-fpn-coco-torch` | RetinaNet | None |
| `yolov8n-coco-torch` | YOLOv8 nano (fast) | ultralytics |
| `yolov8s-coco-torch` | YOLOv8 small | ultralytics |
| `yolov8m-coco-torch` | YOLOv8 medium | ultralytics |
| `yolov8l-coco-torch` | YOLOv8 large | ultralytics |
| `yolov8x-coco-torch` | YOLOv8 extra-large | ultralytics |

### Classification Models

| Model | Description | Extra Deps |
|-------|-------------|------------|
| `resnet50-imagenet-torch` | ResNet-50 | None |
| `mobilenet-v2-imagenet-torch` | MobileNet v2 | None |
| `vit-base-patch16-224-imagenet-torch` | Vision Transformer | None |

### Segmentation Models

| Model | Description | Extra Deps |
|-------|-------------|------------|
| `sam-vit-base-torch` | Segment Anything (base) | segment-anything |
| `sam-vit-large-torch` | Segment Anything (large) | segment-anything |
| `sam-vit-huge-torch` | Segment Anything (huge) | segment-anything |
| `deeplabv3-resnet101-coco-torch` | DeepLabV3 | None |

### Embedding Models

| Model | Description | Extra Deps |
|-------|-------------|------------|
| `clip-vit-base32-torch` | CLIP embeddings | open-clip-torch |
| `dinov2-vits14-torch` | DINOv2 small | None |
| `dinov2-vitb14-torch` | DINOv2 base | None |
| `dinov2-vitl14-torch` | DINOv2 large | None |

## Common Use Cases

### Use Case 1: Run Object Detection

```python
# Verify dataset exists
list_datasets()

# Set context and launch
set_context(dataset_name="my-dataset")
launch_app(dataset_name="my-dataset")

# Apply detection model
execute_operator(
    operator_uri="@voxel51/zoo/apply_zoo_model",
    params={
        "tab": "BUILTIN",
        "model": "faster-rcnn-resnet50-fpn-coco-torch",
        "label_field": "predictions"
    }
)

# View results
set_view(exists=["predictions"])
```

### Use Case 2: Run Classification

```python
set_context(dataset_name="my-dataset")
launch_app(dataset_name="my-dataset")

execute_operator(
    operator_uri="@voxel51/zoo/apply_zoo_model",
    params={
        "tab": "BUILTIN",
        "model": "resnet50-imagenet-torch",
        "label_field": "classification"
    }
)

set_view(exists=["classification"])
```

### Use Case 3: Generate Embeddings

```python
set_context(dataset_name="my-dataset")
launch_app(dataset_name="my-dataset")

execute_operator(
    operator_uri="@voxel51/zoo/apply_zoo_model",
    params={
        "tab": "BUILTIN",
        "model": "clip-vit-base32-torch",
        "label_field": "clip_embeddings"
    }
)
```

### Use Case 4: Compare Ground Truth with Predictions

If dataset has existing labels:

```python
set_context(dataset_name="my-dataset")
dataset_summary(name="my-dataset")  # Check existing fields

launch_app(dataset_name="my-dataset")

# Run inference with different field name
execute_operator(
    operator_uri="@voxel51/zoo/apply_zoo_model",
    params={
        "tab": "BUILTIN",
        "model": "yolov8m-coco-torch",
        "label_field": "predictions"  # Different from ground_truth
    }
)

# View both fields to compare
set_view(exists=["ground_truth", "predictions"])
```

### Use Case 5: Run Multiple Models

```python
set_context(dataset_name="my-dataset")
launch_app(dataset_name="my-dataset")

# Run detection
execute_operator(
    operator_uri="@voxel51/zoo/apply_zoo_model",
    params={
        "tab": "BUILTIN",
        "model": "yolov8n-coco-torch",
        "label_field": "detections"
    }
)

# Run classification
execute_operator(
    operator_uri="@voxel51/zoo/apply_zoo_model",
    params={
        "tab": "BUILTIN",
        "model": "resnet50-imagenet-torch",
        "label_field": "classification"
    }
)

# Run embeddings
execute_operator(
    operator_uri="@voxel51/zoo/apply_zoo_model",
    params={
        "tab": "BUILTIN",
        "model": "clip-vit-base32-torch",
        "label_field": "embeddings"
    }
)
```

## Troubleshooting

**Error: "Dataset not found"**
- Use `list_datasets()` to see available datasets
- Use the **fiftyone-dataset-import** skill to import data first

**Error: "Model not found"**
- Check model name spelling
- Use `get_operator_schema("@voxel51/zoo/apply_zoo_model")` to see available models

**Error: "Missing dependency" (e.g., ultralytics, segment-anything)**
- The MCP server detects missing dependencies
- Response includes `missing_package` and `install_command`
- Install the required package: `pip install <package>`
- Restart MCP server after installing

**Inference is slow**
- Use smaller model variant (e.g., `yolov8n` instead of `yolov8x`)
- Use delegated execution for large datasets
- Consider filtering to a view first

**Out of memory**
- Reduce batch size
- Use smaller model variant
- Process dataset in chunks using views

## Best Practices

1. **Use descriptive field names** - `predictions`, `yolo_detections`, `clip_embeddings`
2. **Don't overwrite ground truth** - Use different field names for predictions
3. **Start with fast models** - Use nano/small variants first, upgrade if needed
4. **Check existing fields** - Use `dataset_summary()` before running inference
5. **Filter first for testing** - Test on a small view before processing full dataset

## Resources

- [FiftyOne Model Zoo](https://docs.voxel51.com/model_zoo/index.html)
- [Applying Models Guide](https://docs.voxel51.com/user_guide/applying_models.html)
- [Zoo Models API](https://docs.voxel51.com/api/fiftyone.zoo.models.html)

---
name: fiftyone-find-duplicates
description: Find duplicate or near-duplicate images in FiftyOne datasets using brain similarity computation. Use when users want to deduplicate datasets, find similar images, cluster visually similar content, or remove redundant samples. Requires FiftyOne MCP server with @voxel51/brain plugin installed.
---

# Find Duplicates in FiftyOne Datasets

## Overview

Find and remove duplicate or near-duplicate images using FiftyOne's brain similarity operators. Uses deep learning embeddings to identify visually similar images.

**Use this skill when:**
- Removing duplicate images from datasets
- Finding near-duplicate images (similar but not identical)
- Clustering visually similar images
- Cleaning datasets before training

## Prerequisites

- FiftyOne MCP server installed and running
- `@voxel51/brain` plugin installed and enabled
- Dataset with image samples loaded in FiftyOne

## Key Directives

**ALWAYS follow these rules:**

### 1. Set context first
```python
set_context(dataset_name="my-dataset")
```

### 2. Launch FiftyOne App
Brain operators are delegated and require the app:
```python
launch_app()
```
Wait 5-10 seconds for initialization.

### 3. Discover operators dynamically
```python
# List all brain operators
list_operators(builtin_only=False)

# Get schema for specific operator
get_operator_schema(operator_uri="@voxel51/brain/compute_similarity")
```

### 4. Compute embeddings before finding duplicates
```python
# ✅ CORRECT
execute_operator(
    operator_uri="@voxel51/brain/compute_similarity",
    params={"brain_key": "img_sim"}
)
# Then find duplicates

# ❌ WRONG - Cannot find duplicates without embeddings
execute_operator(operator_uri="@voxel51/brain/find_duplicates")
```

### 5. Close app when done
```python
close_app()
```

## Complete Workflow

### Step 1: Setup
```python
# Set context
set_context(dataset_name="my-dataset")

# Launch app (required for brain operators)
launch_app()
```

### Step 2: Verify Brain Plugin
```python
# Check if brain plugin is available
list_plugins(enabled=True)

# If not installed:
download_plugin(
    url_or_repo="voxel51/fiftyone-plugins",
    plugin_names=["@voxel51/brain"]
)
enable_plugin(plugin_name="@voxel51/brain")
```

### Step 3: Discover Brain Operators
```python
# List all available operators
list_operators(builtin_only=False)

# Get schema for compute_similarity
get_operator_schema(operator_uri="@voxel51/brain/compute_similarity")

# Get schema for find_duplicates
get_operator_schema(operator_uri="@voxel51/brain/find_duplicates")
```

### Step 4: Compute Similarity
```python
# Execute operator to compute embeddings
execute_operator(
    operator_uri="@voxel51/brain/compute_similarity",
    params={
        "brain_key": "img_duplicates",
        "model": "mobilenet-v2-imagenet-torch"
    }
)
```

**Note:** This takes several minutes depending on dataset size.

### Step 5: Find Duplicates
```python
# Find near-duplicates (95% similarity)
execute_operator(
    operator_uri="@voxel51/brain/find_duplicates",
    params={
        "brain_key": "img_duplicates",
        "thresh": 0.95,
        "method": "representative"
    }
)
```

**Threshold guidelines:**
- `1.0` = Exact duplicates only
- `0.95` = Near duplicates (recommended)
- `0.90` = Similar images
- `0.85` = Loosely similar

### Step 6: Review Results
```python
# Get dataset summary
get_dataset_summary(dataset_name="my-dataset")

# Create view of duplicates
set_context(
    dataset_name="my-dataset",
    view_stages=[
        {"$match": {"duplicates": {"$exists": True, "$ne": []}}}
    ]
)
```

### Step 7: Delete Duplicates
```python
# After reviewing, delete duplicate samples
execute_operator(
    operator_uri="@voxel51/utils/delete_samples",
    params={"target": "current_view"}
)
```

### Step 8: Clean Up
```python
# Close the app
close_app()

# Verify results
set_context(dataset_name="my-dataset")
get_dataset_summary(dataset_name="my-dataset")
```

## Common Use Cases

### Use Case 1: Remove Exact Duplicates
For accidentally duplicated files:
```python
set_context(dataset_name="my-dataset")
launch_app()

execute_operator(
    operator_uri="@voxel51/brain/compute_similarity",
    params={"brain_key": "exact"}
)

execute_operator(
    operator_uri="@voxel51/brain/find_duplicates",
    params={"brain_key": "exact", "thresh": 1.0}
)

close_app()
```

### Use Case 2: Find Unique Samples
Select diverse subset of N unique images:
```python
set_context(dataset_name="my-dataset")
launch_app()

execute_operator(
    operator_uri="@voxel51/brain/compute_similarity",
    params={"brain_key": "unique"}
)

execute_operator(
    operator_uri="@voxel51/brain/find_unique",
    params={
        "brain_key": "unique",
        "num_samples": 1000,
        "method": "greedy"
    }
)

close_app()
```

### Use Case 3: Sort by Similarity
Find images similar to a specific sample:
```python
set_context(dataset_name="my-dataset")
launch_app()

execute_operator(
    operator_uri="@voxel51/brain/compute_similarity",
    params={"brain_key": "search"}
)

execute_operator(
    operator_uri="@voxel51/brain/sort_by_similarity",
    params={
        "brain_key": "search",
        "query_id": "sample_id_here",
        "k": 20
    }
)

close_app()
```

## Key Brain Operators

Use `get_operator_schema()` to see full parameters:

- `@voxel51/brain/compute_similarity` - Compute embeddings and similarity index
- `@voxel51/brain/find_duplicates` - Find duplicate/near-duplicate samples
- `@voxel51/brain/find_unique` - Find diverse unique samples
- `@voxel51/brain/sort_by_similarity` - Sort by similarity to query
- `@voxel51/brain/compute_visualization` - Create 2D/3D visualizations

## Troubleshooting

**Error: "No executor available"**
- Cause: FiftyOne App not running
- Solution: Call `launch_app()` and wait 10 seconds

**Error: "Brain key not found"**
- Cause: Embeddings not computed
- Solution: Run `compute_similarity` first

**Error: "Operator not found"**
- Cause: Brain plugin not installed
- Solution: Install with `download_plugin()` and `enable_plugin()`

**Error: "Missing dependency" (e.g., torch, tensorflow)**
- The MCP server detects missing dependencies automatically
- You'll receive structured error with package name and install command
- **Auto-install**: Offer to run the install command for the user
- Example: `pip install torch torchvision`
- After installation, retry the operator

**Similarity computation is slow**
- Use faster model: `mobilenet-v2-imagenet-torch`
- Use GPU if available
- Process large datasets in batches

## Best Practices

1. **Start with high threshold** (0.95) and adjust lower as needed
2. **Always review before deleting** - Use views to inspect duplicates
3. **Use representative method** - Keeps highest quality samples
4. **Store embeddings** - Reuse for multiple operations via `brain_key`
5. **Discover dynamically** - Use `list_operators()` and `get_operator_schema()`

## Performance Notes

**Embedding computation time:**
- 1,000 images: ~1-2 minutes
- 10,000 images: ~10-15 minutes
- 100,000 images: ~1-2 hours

**Memory requirements:**
- ~2KB per image for embeddings
- ~4-8KB per image for similarity index

## Resources

- Use `get_operator_schema()` to see operator parameters
- [FiftyOne Brain Documentation](https://docs.voxel51.com/user_guide/brain.html)
- [Brain Plugin Source](https://github.com/voxel51/fiftyone-plugins/tree/main/plugins/brain)

## License

Copyright 2017-2025, Voxel51, Inc.
Apache 2.0 License

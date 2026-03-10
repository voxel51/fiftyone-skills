# Data Quality Checks

Deep-dive quality audit for any FiftyOne dataset. All field references are discovered dynamically — never hardcoded.

---

## Prerequisites

Before running any quality check:

```
dataset_summary()
get_field_schema(flat=True)
```

Confirm media type. Quality checks apply to image datasets directly; for video datasets, checks apply per-frame or per-sample depending on the metric.

---

## 1. Metadata Computation

Compute metadata for all samples. This is required before any resolution, aspect ratio, or file size check.

```
list_operators(builtin_only=False)
get_operator_schema(operator_uri="@voxel51/utils/compute_metadata")
execute_operator(operator_uri="@voxel51/utils/compute_metadata", params={})
```

After completion, verify metadata fields are populated:
```
get_field_schema(flat=True)
bounds("metadata.width")
```

If `metadata.width` returns null → metadata computation failed. Check that media files are accessible at their `filepath` paths.

---

## 2. Corruption Detection

Samples where metadata computation fails have null metadata — these indicate corrupted or missing files.

```
set_view(filters={"metadata": null})
```

Report the count. If any corrupted samples exist:
1. Show the sample count to the user
2. Ask for confirmation before tagging
3. Tag confirmed:
   ```
   tag_samples(["corrupted"])
   ```
4. Offer to exclude from curation:
   ```
   # Python SDK guidance
   clean_view = dataset.match(F("metadata") != None)
   ```

---

## 3. Resolution Filtering

### Bounds check
```
bounds("metadata.width")
bounds("metadata.height")
```

### Distribution
```
histogram_values("metadata.width", bins=20)
histogram_values("metadata.height", bins=20)
```

### Filtering low-resolution samples

Use ViewField expressions (Python SDK) to build a filtered view:
```python
from fiftyone import ViewField as F

min_width  = 224    # adjust to dataset requirements
min_height = 224

resolution_view = dataset.match(
    (F("metadata.width") >= min_width) &
    (F("metadata.height") >= min_height)
)
```

Report to user:
- Total samples
- Samples below resolution threshold
- Ask before tagging low-resolution samples as `"low_resolution"`

---

## 4. Aspect Ratio Filtering

Identify panoramic (very wide) and portrait-extreme (very tall) images that may indicate scanning artifacts, incorrect crops, or data pipeline errors.

```python
from fiftyone import ViewField as F

# Samples wider than 2× their height
long_filter = F("metadata.width") > 2 * F("metadata.height")

# Samples taller than 2× their width
tall_filter  = F("metadata.height") > 2 * F("metadata.width")

# Normal aspect ratio
normal_aspect = (~long_filter) & (~tall_filter)

# Views
panoramic_view     = dataset.match(long_filter)
tall_view          = dataset.match(tall_filter)
normal_aspect_view = dataset.match(normal_aspect)
```

Report counts for each category. Offer to tag outliers after confirmation:
```
tag_samples(["aspect_outlier"])
```

---

## 5. File Size Filtering

Very small files may be placeholder images, blank frames, or download artifacts.

```
bounds("metadata.size_bytes")
mean("metadata.size_bytes")
std("metadata.size_bytes")
histogram_values("metadata.size_bytes", bins=20)
```

Flag samples where `size_bytes` is below a heuristic threshold (e.g., < 5 KB for images expected to be natural scenes). Present to user before tagging.

```python
from fiftyone import ViewField as F
tiny_view = dataset.match(F("metadata.size_bytes") < 5000)
```

---

## 6. Color Channel Check

Grayscale images in RGB datasets can cause silent model errors if not expected.

```python
from fiftyone import ViewField as F

# Find grayscale samples in an otherwise RGB dataset
grayscale_view = dataset.match(F("metadata.num_channels") != 3)
```

Report count and sample IDs. Offer to tag as `"grayscale"` after confirmation.

---

## 7. Comprehensive Image Quality (jacobmarks/image_issues plugin)

The `jacobmarks/image_issues` plugin is the **primary and recommended** method for a full image quality audit. It detects multiple quality dimensions in one pass: blurriness, brightness extremes, contrast issues, entropy, saturation, and aspect ratio anomalies.

**Do NOT use custom cv2 code.** Always use this plugin.

### Step 1: Discover the installed plugin name

Plugin names in documentation may differ from what is actually installed. Always discover dynamically:

```
list_plugins()
```

Look for an entry matching "image_issues" or "image-quality". Note the **exact installed name** — use this in all subsequent calls. Common installed names:
- `@jacobmarks/image_issues` (most common)
- `image_issues`

### Step 2: Download and enable (if not installed)

If the plugin is not in the `list_plugins()` output:
```
download_plugin(plugin_name="jacobmarks/image-quality-issues")
```

Then confirm the installed name:
```
list_plugins()
enable_plugin(plugin_name="<exact_name_from_list_plugins>")
```

### Step 3: Discover operator URIs

```
list_operators(builtin_only=False)
```

Find operators from the image_issues plugin. Common operators (URIs may vary — use what `list_operators()` returns):
- `@jacobmarks/image_issues/find_issues` — run all or individual checks
- `@jacobmarks/image_issues/compute_blurriness`
- `@jacobmarks/image_issues/compute_brightness`
- `@jacobmarks/image_issues/compute_contrast`
- `@jacobmarks/image_issues/compute_entropy`
- `@jacobmarks/image_issues/compute_saturation`
- `@jacobmarks/image_issues/compute_aspect_ratio`

**Always confirm URIs from `list_operators()` output. Do not assume from documentation.**

### Step 4: Check delegated service

Brain operators require the delegated service to be running:
```bash
fiftyone delegated list
# If empty or not running:
fiftyone delegated launch &
```
Wait ~5 seconds after starting.

### Step 5: Run quality checks (one issue at a time)

Run each issue check separately with `delegate=True`. Wait for each to complete before starting the next.

```
# Get operator schema to verify params
get_operator_schema(operator_uri="@jacobmarks/image_issues/find_issues")

# Run blurriness check
execute_operator(
    operator_uri="@jacobmarks/image_issues/find_issues",
    params={"issue_mode": "SINGLE", "issue": "blurry"},
    delegate=True
)
```

Monitor progress:
```
list_delegated_operations()
```

Wait until status is `"COMPLETED"` before running the next check.

Repeat for each issue type (adjust based on `get_operator_schema()` output):
```
{"issue_mode": "SINGLE", "issue": "low_contrast"}
{"issue_mode": "SINGLE", "issue": "low_saturation"}
{"issue_mode": "SINGLE", "issue": "weird_aspect_ratio"}
{"issue_mode": "SINGLE", "issue": "dark"}
{"issue_mode": "SINGLE", "issue": "bright"}   # See threshold note below
```

### Step 6: Inspect results

After execution, check what boolean fields were added:
```
get_field_schema(flat=True)
```

The plugin adds per-sample boolean flag fields for each quality dimension (e.g., `blurry: True/False`, `low_contrast: True/False`). Use `count_values` on these fields to understand impact:

```
count_values("blurry")
count_values("low_contrast")
count_values("low_saturation")
count_values("weird_aspect_ratio")
```

### Step 7: Create insight views

For each quality flag field discovered via `get_field_schema()`, create a named view. View names are suggestions — adapt to the dataset:
```python
# Python SDK guidance — field names come from get_field_schema(), not hardcoded
from fiftyone import ViewField as F

for flag_field in discovered_quality_fields:   # from get_field_schema() output
    view_name = f"{flag_field}_samples"
    dataset.save_view(view_name, dataset.match(F(flag_field) == True))
    # Then load each in App for interactive review:
    # execute_operator("@voxel51/operators/load_saved_view", params={"name": view_name})
```

Offer to tag flagged samples after user reviews them in the App:
```
tag_samples(["quality_issue"])
```

### Note on `bright` flag

The `bright` threshold is calibrated for general-purpose datasets. For well-lit datasets (food photos, product images, studio shots), it may flag a large percentage (up to 100%) of samples as `bright`. This is a **known calibration artifact** — it does not mean the images are overexposed. In these cases:
- Do NOT use the `bright` flag as a quality filter
- Rely on `dark`, `blurry`, `low_contrast`, and `low_saturation` instead
- Inform the user if `bright` flags > 80% of samples

---

## 8. Brightness Analysis (fallback)

> **Skip this section if the `jacobmarks/image_issues` plugin was run** — brightness extremes and exposure are already covered by the plugin.

If the plugin is not available and metadata mean values exist:

```
mean("metadata.mean")
std("metadata.mean")
histogram_values("metadata.mean", bins=20)
```

- Very low mean (< 30 for 8-bit) → potentially underexposed / night images
- Very high mean (> 225) → overexposed / blown-out
- Bimodal distribution → two distinct lighting conditions (day + night)

Offer to tag if these represent quality issues or valid domain subsets (e.g., `"night"` intentionally).

---

## 9. Tag-and-Review Pattern

After flagging samples in any quality check:

1. **Tag** samples with a descriptive tag (e.g., `"corrupted"`, `"low_resolution"`, `"blurry"`, `"aspect_outlier"`)
   ```
   tag_samples(["<quality_tag>"])
   ```
2. **Review in App** — direct user to the FiftyOne App (use get_session_info() to get the URL)
3. **Confirm action** — ask whether to:
   - Exclude from downstream views (`dataset.exclude_by("tags", "<quality_tag>")`)
   - Delete permanently (`dataset.delete_samples(view)` — only after explicit confirmation)
   - Keep but track (leave tagged)

---

## 10. CLIPScore Alignment (Captioned / Multimodal Datasets)

For datasets that have both images and text captions (e.g., image-caption pairs, VQA datasets):

**Purpose**: Detect misaligned caption-image pairs where the caption does not describe the image.

### Prerequisite
A CLIP similarity index must exist or be computed first (Phase 5 of SKILL.md).

### Workflow

```
list_operators(builtin_only=False)
```

If `@voxel51/brain/compute_similarity` with CLIP is available:

1. Compute CLIP embeddings for images
2. Use `sort_by_similarity` with the caption text to score alignment
3. Flag samples with low similarity scores

**Threshold guideline**: CLIPScore < 21.8 (cosine similarity × 100) indicates poor alignment (from published CLIP research). Tune to dataset.

### Tagging low-alignment samples
```
tag_samples(["low_clip_alignment"])
```

---

## 11. Export Clean Subset

After all quality filters are applied and confirmed:

```python
# Python SDK guidance
from fiftyone import ViewField as F

# Discover quality flag fields via get_field_schema() first — do not hardcode
# Then build the filter from discovered fields:
quality_filters = (
    (F("blurry") == False) &
    (F("low_contrast") == False) &
    (F("low_saturation") == False) &
    (F("weird_aspect_ratio") == False)
)

# Add uniqueness filter if computed
# quality_filters = quality_filters & (F("uniqueness") >= 0.3)

clean_view = dataset.match(quality_filters)

# Save named view
dataset.save_view(f"{dataset.name}_clean", clean_view)

# Clone to a new persistent dataset (confirm with user first)
clean_dataset = clean_view.clone(
    name=f"{dataset.name}_clean",
    persistent=True
)
```

Confirm the clone with the user before executing. Report the final sample count of the clean dataset.

---

## Quality Metrics Summary Table

| Metric | MCP tool | Python SDK alternative |
|--------|----------|----------------------|
| Corruption | `set_view(filters={"metadata": null})` | `match(F("metadata") == None)` |
| Resolution | `bounds("metadata.width/height")` | `match(F("metadata.width") >= N)` |
| Aspect ratio | N/A (ViewField only) | `match(long_filter)` |
| File size | `bounds("metadata.size_bytes")` | `match(F("metadata.size_bytes") < N)` |
| Color channels | N/A (ViewField only) | `match(F("metadata.num_channels") != 3)` |
| Blur, brightness, contrast, saturation | `jacobmarks/image_issues` plugin (preferred) | File-size heuristic fallback |
| Brightness (fallback) | `mean("metadata.mean")` | `match(F("metadata.mean") < N)` |
| CLIPScore | `sort_by_similarity` + CLIP | `compute_similarity` + `sort_by_similarity` |

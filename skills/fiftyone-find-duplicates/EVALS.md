# Evals: fiftyone-find-duplicates

Checks that this skill loads for the right requests and runs the duplicate workflow correctly. Format: [`EVALS.md` format](../../CONTRIBUTING.md#evalsmd-format-optional).

## Setup

Requires FiftyOne, the [FiftyOne MCP server](https://github.com/voxel51/fiftyone-mcp-server), the [`@voxel51/brain`](https://github.com/voxel51/fiftyone-plugins/tree/main/plugins/brain) plugin and `torch`. TC2 and TC3 compute embeddings with `mobilenet-v2-imagenet-torch` inside the MCP server, so install `torch` in the same Python environment as the server.

Run this before TC1, and again before TC2: TC1 deletes samples, and TC3 continues from TC2. It copies the `quickstart` zoo dataset and plants 5 exact duplicates, so every test case has a known answer:

```python
import fiftyone as fo
import fiftyone.brain as fob
import fiftyone.zoo as foz

name = "find-dups-eval"
if fo.dataset_exists(name):
    fo.delete_dataset(name)

dataset = foz.load_zoo_dataset("quickstart").clone(name)
dataset.persistent = True

# Plant 5 exact duplicates: new samples that point at existing image files.
# Originals and copies are both tagged "planted" (10 samples in total).
planted = dataset.take(5, seed=51)
planted.tag_samples("planted")
dataset.add_samples([sample.copy() for sample in planted])

print(len(dataset))  # 205

# Confirm the answer key: exactly the 5 planted groups, no others
assert len(fob.compute_exact_duplicates(dataset)) == 5
```

## Trigger Prompts

### Should trigger

| ID | Prompt |
|----|--------|
| T1 | "Find duplicate images in my dataset" |
| T2 | "i think my scraper saved the same photos more than once, can you clean up street-signs-v2 so each image only shows up once" |
| T3 | "Before we send this batch for labeling, flag any shots that are basically the same picture so we don't pay to annotate them twice" |
| T4 | "Show me which images in the quickstart dataset look almost identical to each other" |
| T5 | "I merged two datasets and some images are in both. Remove the copies but keep one of each" |

### Should not trigger

| ID | Prompt | Better fit |
|----|--------|------------|
| N1 | "My ground_truth detections have several boxes stacked on the same object. Find and clean up the duplicate boxes" | `fiftyone-dataset-curation` (annotation audit) |
| N2 | "Plot my image embeddings in 2D so I can see clusters and outliers" | `fiftyone-embeddings-visualization` |
| N3 | "Pick 50 diverse, representative images from my dataset for a pilot labeling batch" | `fiftyone-dataset-curation` (subset creation) |
| N4 | "Drop the duplicate rows from this annotations CSV before I import it" | None (general data cleaning) |

## Test Cases

### TC1: Remove exact duplicates

**Prompt:** "I accidentally imported some images twice into find-dups-eval. Find the exact duplicates and remove the extra copies."

**Expected result:** The agent finds the 5 planted duplicates by file content and keeps one sample per image.

**Success criteria:**

- [ ] Opens `find-dups-eval` in the App before running brain operators, and runs them on that dataset
- [ ] Uses `@voxel51/brain/find_exact_duplicates`, not similarity embeddings
- [ ] Before deleting, tells the user it found 5 groups (10 samples) and points to the `exact duplicates` saved view for review
- [ ] Ends with 200 samples, of which 5 are tagged `planted`

### TC2: Review near duplicates without deleting

**Prompt:** "Find near-duplicate images in find-dups-eval and show them to me in the App. Don't delete anything yet."

**Expected result:** The agent computes embeddings, finds near duplicates and opens the saved review view.

**Success criteria:**

- [ ] Calls `compute_similarity` with `model`, `backend` and `metric`
- [ ] Passes the same brain key to `find_near_duplicates` as `similarity_index`
- [ ] Loads the `near duplicates` saved view and does not filter on a `near_dup_id` field
- [ ] If `set_view` reports no App execution context, tells the user to open `near duplicates` from the App's saved-view dropdown
- [ ] The `near duplicates` view includes all 10 samples tagged `planted`
- [ ] Deletes nothing: the dataset still has 205 samples

### TC3: Tighten the threshold

**Prompt (follow-up to TC2):** "That flagged too many images. Only show me ones that are almost identical."

**Expected result:** The agent reruns `find_near_duplicates` with a lower threshold on the existing embeddings.

**Success criteria:**

- [ ] Lowers the threshold, for example to `0.1`. Thresholds are distances, so lower is stricter
- [ ] Reuses the existing brain key instead of calling `compute_similarity` again
- [ ] The new results still include all 10 samples tagged `planted`

## Known Failure Modes

Failures seen before. Each is fixed in `SKILL.md`; the test case listed catches it if it comes back.

| Failure | Symptom | Caught by | Fixed in |
|---------|---------|-----------|----------|
| Calls `compute_similarity` without `backend` and `metric` | Validation error for the missing `backend`, then for the missing `metric` | TC2 | [#55](https://github.com/voxel51/fiftyone-skills/pull/55) |
| Filters on a `near_dup_id` field | Empty view: `find_near_duplicates` creates saved views, not that field | TC2 | [#55](https://github.com/voxel51/fiftyone-skills/pull/55) |
| `set_view` has no App execution context | The tool errors and the user never sees the duplicates | TC2 | [#55](https://github.com/voxel51/fiftyone-skills/pull/55) |

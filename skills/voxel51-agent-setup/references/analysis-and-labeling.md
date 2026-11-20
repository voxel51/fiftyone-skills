# Analysis & labeling

Every computation here writes real results to the dataset and is fully reachable.
Where a capability also has an interactive App panel (embeddings scatter plot, data
quality review UI, a dashboard chart), that panel's rendering is a human, browser-only
experience — only the underlying computation and its results are reachable here.

Call `list_operators(query=...)` for the current operator in each area below — it's
live, permission-filtered, ranked, and includes each result's description. Search
keywords by area:

- **Brain methods** — "compute visualization", "compute similarity", "sort by
  similarity", "compute uniqueness", "compute mistakenness", "compute hardness",
  "find duplicates", "deduplicate"
- **Similarity search** — "similarity search", "list similarity runs"
- **Model evaluation** — "evaluate model", "evaluation info", "evaluation scenario"
- **Data Quality** — "data quality scan", "blurriness", "brightness", "aspect
  ratio", "entropy", "near duplicates"
- **Auto-Labeling** — "auto label", "zoo models for labeling"
- **Agentic Labeling** — "agentic labeler run", "agentic labeler agent", "agentic
  labeler test"
- **Annotation (CVAT/Labelbox etc.)** — "request annotations", "annotation info"
- **Zoo models** — "load zoo dataset", "apply zoo model"
- **Label schemas** — "label schema doc", "label schema attributes"
- **Workflows (multi-stage pipelines)** — "create workflow", "run workflow",
  "workflow stage". A workflow is built from 25+ `*_stage` operators (e.g. filter
  labels, match tags, model, auto-label, review) — the visual canvas for building
  one is browser-only, but creating and running a workflow through these operators
  directly works the same either way.
- **Dashboard** — "configure plot", "dashboard". Configuring a chart's data works
  headlessly; watching it render doesn't apply here.

## Known gotchas not visible from a search result or schema alone

- `compute_uniqueness`/`compute_mistakenness`/`compute_hardness` download a small
  built-in model on first use; some environments' background-job executors run
  with a read-only filesystem that blocks that download. If one fails with a
  filesystem error, that's an environment/infra issue, not a bad call.
- `get_brain_info` and `get_annotation_info` both need a real run/annotation key —
  a bare call with none returns a validation error asking for one, not a list.
  Discover existing keys through a similarity-runs listing operator, or by asking
  the user which run they mean.

# Datasets & samples

The core SDK surface — dataset state, no live App session required. Call
`list_operators(query=...)` to find the current operator for what you need —
it's live, permission-filtered, ranked, and already includes each result's
description, so a maintained inventory here would only go stale (the old one
already had). Confirm exact arguments with `get_operator_schema` before
calling any of them. Search keywords by area (one example operator per area
as a starting anchor if search turns up nothing):

- **Dataset lifecycle** — "create dataset", "rename dataset", "clone dataset",
  "delete samples" (e.g. `@voxel51/utils/create_dataset`)
- **Views & saved views** — "apply saved view", "save view", "list saved
  views" (e.g. `@voxel51/operators/save_view`)
- **Fields & schema** — "field schema", "clone field", "rename field",
  "dynamic fields" (e.g. `@voxel51/operators/get_field_schema`)
- **Sample & label editing** — "clone selected samples", "delete selected
  labels" (e.g. `@voxel51/operators/delete_selected_samples`)
- **Indexes & summary fields** — "create index", "summary field" (e.g.
  `@voxel51/operators/create_index`)
- **Group slices** — "add group slice", "rename group slice" (e.g.
  `@voxel51/operators/add_group_slice`)
- **Media import** — "import media", "compute metadata", "lerobot import"
  (e.g. `@voxel51/operators/import_media_upload`)
- **Workspaces** — "save workspace", "load workspace" (e.g.
  `@voxel51/operators/save_workspace`)
- **Files** — "list files", "download file" (e.g. `@voxel51/operators/list_files`)

## Known gotchas not visible from a search result or schema alone

`manage_indexes` has a dynamic form — a call naming no field to create or drop
returns the operator's own "nothing to do" notice rather than an error. Name a
real field (confirm with `get_field_schema` first) to get a useful result.

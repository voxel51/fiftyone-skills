# Datasets & samples

The core SDK surface — dataset state, no live App session required. Confirm exact
arguments with `get_operator_schema` before calling any of these.

## Dataset lifecycle
`@voxel51/utils/create_dataset`, `load_dataset`, `edit_dataset_info`, `rename_dataset`,
`clone_dataset`, `delete_dataset`, `delete_samples`

## Views & saved views
- Apply a saved view: `@voxel51/utils/apply_saved_view`
- Manage saved views: `@voxel51/operators/list_saved_views`, `load_saved_view`,
  `reload_saved_view`, `save_view`, `edit_saved_view_info`, `delete_saved_view`

## Fields & schema
- Inspect: `@voxel51/operators/get_field_schema`
- Edit: `edit_field_info`, `edit_field_values`
- Clone/rename: `clone_sample_field`, `clone_frame_field`, `rename_sample_field`,
  `rename_frame_field`
- Clear/delete: `clear_sample_field`, `clear_frame_field`, `delete_sample_field`,
  `delete_frame_field`
- Dynamic fields: `add_dynamic_sample_fields`, `add_dynamic_frame_fields`,
  `remove_dynamic_sample_fields`, `remove_dynamic_frame_fields`
(all under `@voxel51/operators/`)

## Sample & label editing
`@voxel51/operators/clone_selected_samples`, `delete_selected_samples`,
`delete_selected_labels`

## Indexes & summary fields
`@voxel51/operators/create_index`, `drop_index`, `create_summary_field`,
`update_summary_field`, `delete_summary_field`; `@voxel51/indexes/manage_indexes`;
`@voxel51/panels/create_index_or_summary_field`

Note: `manage_indexes` has a dynamic form — a call naming no field to create or drop
returns the operator's own "nothing to do" notice rather than an error. Name a real
field (confirm with `get_field_schema` first) to get a useful result.

## Group slices
`@voxel51/operators/add_group_slice`, `rename_group_slice`, `delete_group_slice`

## Media import
`@voxel51/operators/prepare_media_upload`, `check_media_import`,
`delete_media_upload`, `import_media_upload`, `import_media_upload_now`,
`plan_lerobot_import`, `import_lerobot_source`; `@voxel51/utils/compute_metadata`,
`generate_thumbnails`

## Workspaces (saved Spaces layouts)
`@voxel51/operators/list_workspaces`, `load_workspace`, `save_workspace`,
`edit_workspace_info`, `delete_workspace`

## Files
`@voxel51/operators/list_files`, `list_subdirs`, `download_file`

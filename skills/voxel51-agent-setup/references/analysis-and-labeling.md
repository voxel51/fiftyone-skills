# Analysis & labeling

Every computation here writes real results to the dataset and is fully reachable.
Where a capability also has an interactive App panel (embeddings scatter plot, data
quality review UI, a dashboard chart), that panel's rendering is a human, browser-only
experience — only the underlying computation and its results are reachable here.

## Brain methods
`@voxel51/brain/compute_visualization`, `compute_similarity`, `sort_by_similarity`,
`add_similar_samples`, `compute_uniqueness`, `compute_mistakenness`,
`compute_hardness`, `find_exact_duplicates`, `deduplicate_exact_duplicates`,
`find_near_duplicates`, `deduplicate_near_duplicates`, `get_brain_info`,
`load_brain_view`, `rename_brain_run`, `delete_brain_run`

Note: `compute_uniqueness`/`compute_mistakenness`/`compute_hardness` download a small
built-in model on first use; some environments' background-job executors run with a
read-only filesystem that blocks that download. If one fails with a filesystem error,
that's an environment/infra issue, not a bad call.

`get_brain_info` needs a real `brain_key` — a bare call with none returns a validation
error asking for one, not a list. Discover existing keys through
`@voxel51/panels/list_similarity_runs` or by asking the user which brain run they mean.

## Similarity search
`@voxel51/panels/similarity_search`, `list_similarity_runs`, `init_similarity_run`

## Model evaluation
`@voxel51/evaluation/evaluate_model`, `get_evaluation_info`, `load_evaluation_view`,
`rename_evaluation`, `delete_evaluation`; `@voxel51/panels/evaluate_model_async`,
`model_evaluation_configure_scenario`, `mes_plot_resolver`, `list_me_scenarios`

## Data Quality
`@voxel51/panels/dq_init_run`, `dq_scan_pipeline`, `dq_scan_init`, `dq_scan_compute`,
`dq_scan_finalize`, `list_dq_runs`, `dq_set_status`, `dq_delete_results`,
`compute_blurriness`, `compute_brightness`, `compute_aspect_ratio`, `compute_entropy`,
`compute_exact_duplicates`, `compute_near_duplicates`

## Auto-Labeling
`@voxel51/panels/al_init_run`, `byol_init_run`, `al_generate_labels`,
`al_generate_labels_init`, `al_generate_labels_finalize`, `al_generate_labels_pipeline`,
`al_get_allowed_zoo_models`, `list_al_runs`, `verified_auto_label`,
`verified_analyze_label`

## Agentic Labeling
`@voxel51/agentic-labeler/run_labeling`, `agentic_labeler_create_run`,
`agentic_labeler_list_runs`, `agentic_labeler_get_run`, `agentic_labeler_update_run`,
`agentic_labeler_delete_run`, `agentic_labeler_pause_run`, `agentic_labeler_resume_run`,
`agentic_labeler_cancel_run`, `agentic_labeler_create_agent`,
`agentic_labeler_list_agents`, `agentic_labeler_get_agent`,
`agentic_labeler_update_agent`, `agentic_labeler_delete_agent`,
`agentic_labeler_get_model_availability`, `agentic_labeler_find_similar_samples`,
full lifecycle including test/eval: `agentic_labeler_submit_test`,
`agentic_labeler_get_test_results`, `agentic_labeler_cancel_test`

## Annotation (CVAT/Labelbox etc.)
`@voxel51/annotation/request_annotations`, `load_annotations`, `get_annotation_info`,
`load_annotation_view`, `rename_annotation_run`, `delete_annotation_run`

`get_annotation_info` needs a real annotation run key, same pattern as `get_brain_info`
above — don't call it bare expecting a list.

## Zoo models
`@voxel51/zoo/load_zoo_dataset`, `apply_zoo_model`

## Label schemas
`@voxel51/label-schemas/list_label_schema_docs`, `get_label_schema_doc`,
`create_label_schema_doc`, `update_label_schema_doc`, `propagate_label_schema_field`,
`delete_label_schema_doc`, `list_undeclared_label_schema_attributes`,
`declare_label_schema_attributes`

## Workflows (multi-stage pipelines)
`@voxel51/workflows/create_workflow`, `list_workflows`, `get_workflow`,
`update_workflow`, `clone_workflow`, `delete_workflow`, `run_workflow`,
`workflow_progress`. A workflow is built from 25+ `*_stage` operators (e.g.
`filter_labels_stage`, `match_tags_stage`, `model_stage`, `auto_label_stage`,
`review_stage`) — the visual canvas for building one is browser-only, but creating and
running a workflow through these operators directly works the same either way.

## Dashboard
`@voxel51/dashboard/configure_plot`, `dashboard`. Configuring a chart's data works
headlessly; watching it render doesn't apply here.

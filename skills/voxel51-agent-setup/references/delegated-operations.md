# Delegated (background) operations

## Running something in the background
Any operator can be queued instead of run inline:
`execute_operator(operator_uri, ..., delegate=True)`. Check the response's
`delegated` field — not every operator supports delegation, and a `false` means it
ran inline instead. A successful delegated call returns a real `operation_id`; the
run executes on a separate executor, independent of the calling session.

## Checking on your own runs
- `list_delegated_operations(run_state=..., limit=...)` — your own background-run
  history. Optional `run_state` filter (e.g. `"COMPLETED"`, `"FAILED"`, `"RUNNING"`).
- `get_delegated_operation(operation_id)` — one run's current status and, once
  complete, its result or error. If a run you know completed still reports
  "no operation found," that's a sign this deployment's gateway is on an older
  build — ask the user to check with their FiftyOne admin about updating it, rather
  than assuming the run itself failed.

## Delegated-run metadata (read-only)
`@voxel51/runs/get_run_info`, `load_run_view`, `rename_run`, `delete_run`

## What you can't do here yet
Admin actions on a delegated operation — rerunning it, archiving it, pinning it,
relabeling it, or forcing it to a failed state — aren't reachable through this
gateway. They're GraphQL-only on the Voxel51 platform side, with no corresponding
operator. If a user asks to rerun or archive a specific run, tell them this isn't
available through the connected agent yet and point them at the App's own Runs tab.

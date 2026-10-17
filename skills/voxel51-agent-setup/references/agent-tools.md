# The FiftyOne Agent's own operators

These are the operators behind the in-app Voxel51 Agent chat panel. Reachable the
same way as any other operator — the connected user's own account still has to be
permitted to run them.

## Conversations
`@voxel51/fiftyone-agent/create_conversation`, `switch_conversation`,
`delete_conversation`, `rename_conversation`, `export_conversation`

## Chat / turn management
`@voxel51/fiftyone-agent/send_message`, `cancel_operation`, `confirm_pipeline`,
`replay_tool_call`

## LLM configuration
`@voxel51/fiftyone-agent/load_config`, `save_config`, `get_providers`,
`test_connection`

## Code execution
`@voxel51/fiftyone-agent/write_code`, `execute_code` — runs Python against
`ctx.dataset`/`ctx.view`. Stateless; no chat-session dependency, callable standalone.
Internally marked a dangerous-risk operator; this gateway doesn't currently gate on
that risk level beyond the normal permission check, so use it deliberately, not as a
default way to answer a question another operator could answer more narrowly.

## Plugin authoring from chat
`@voxel51/fiftyone-agent/write_plugin`, `test_plugin`, `publish_plugin`,
`discard_plugin` — `write_plugin` ties ownership of the draft to the active
conversation id. Calling it outside a conversation this same caller created may
behave unexpectedly; prefer running these as part of one continuous conversation
rather than isolated one-off calls.

## Skill authoring from chat
`@voxel51/fiftyone-agent/read_skill`, `write_skill`, `save_skill`, `delete_skill` —
likely share the same conversation-scoped draft pattern as plugin authoring above.

## Memory & instructions (operator-level)
`@voxel51/fiftyone-agent/load_memory`, `save_memory`, `clear_history`,
`load_instructions`, `save_instructions` — these are real, reachable operators.

They are **not** the same thing as the in-app Agent's internal memory system (a
separate three-tier read/write/rewrite tool set hardcoded into its own LLM loop,
with no operator of its own) — that internal system isn't reachable through this
gateway at all, by any means, regardless of permissions.

## Usage & status
`@voxel51/fiftyone-agent/get_usage_metrics`, `get_delegated_ops_status`

## Not reachable from here
`get_selected_media` depends on a live, connected App session (what's currently
selected right now) — same category as the App-session-only actions below, not
something this gateway can answer since there's no "current" selection on a
stateless server.

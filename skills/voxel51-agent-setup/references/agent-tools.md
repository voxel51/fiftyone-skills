# The FiftyOne Agent's own operators

These are the operators behind the in-app Voxel51 Agent chat panel. Reachable the
same way as any other operator — the connected user's own account still has to be
permitted to run them. Call `list_operators(query=...)` to find the current ones —
try "conversation", "send message", "LLM config", "execute code", "write plugin",
"write skill", "save memory", "usage metrics".

## Known gotchas not visible from a search result or schema alone

- **Code execution** (`execute_code`) runs Python against `ctx.dataset`/`ctx.view`.
  Stateless; no chat-session dependency, callable standalone. Internally marked a
  dangerous-risk operator; this gateway doesn't currently gate on that risk level
  beyond the normal permission check, so use it deliberately, not as a default way
  to answer a question another operator could answer more narrowly.
- **Plugin authoring from chat** (`write_plugin` and friends) ties ownership of the
  draft to the active conversation id. Calling it outside a conversation this same
  caller created may behave unexpectedly; prefer running these as part of one
  continuous conversation rather than isolated one-off calls. Skill authoring
  (`read_skill`/`write_skill`/`save_skill`/`delete_skill`) likely shares the same
  conversation-scoped draft pattern.
- **Memory & instructions operators** (`load_memory`, `save_memory`,
  `load_instructions`, `save_instructions`) are real, reachable operators — but
  they are **not** the same thing as the in-app Agent's internal memory system (a
  separate three-tier read/write/rewrite tool set hardcoded into its own LLM loop,
  with no operator of its own). That internal system isn't reachable through this
  gateway at all, by any means, regardless of permissions.
- **`get_selected_media`** depends on a live, connected App session (what's
  currently selected right now) — same category as the live App-session actions in
  [`not-available.md`](not-available.md), not something this gateway can answer
  since there's no "current" selection on a stateless server.

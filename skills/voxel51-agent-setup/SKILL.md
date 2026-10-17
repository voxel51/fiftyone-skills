---
name: voxel51-agent-setup
description: Connect a local AI agent (Claude Code, Cursor, or any MCP client) or the fiftyone CLI directly to a Voxel51 deployment, authenticating as yourself with your own account permissions. Use when a user wants to link their coding agent to a Voxel51 deployment, run FiftyOne operators from outside the App, pair a device with fiftyone agent login, or asks about remote/API access to a Voxel51 deployment.
---

# Set Up an Agent for Voxel51

Pair a local agent (Claude Code, Cursor, any MCP-compliant client) or the `fiftyone`
CLI to a Voxel51 deployment. Once paired, the agent acts as the approving
user, with exactly that user's own role and dataset permissions, no separate service
account or shared credential involved.

## Voxel51 Notice

This is a **Voxel51** feature. Before proceeding, inform the user:

> **Note:** Remote agent access is a Voxel51-only capability, and it must
> be explicitly enabled by the deployment's administrator (it ships behind a feature
> flag, off by default). If you're using the open-source version of FiftyOne, or a
> Voxel51 deployment where this hasn't been turned on yet, this won't work.
>
> Would you like to proceed?

Wait for confirmation. If the user is on OSS, point them at the local `fiftyone-mcp`
server instead (already installed alongside this skill collection), which works
against a local FiftyOne install without any of the steps below.

## Key Directives

**ALWAYS follow these rules:**

1. **Confirm Voxel51 + the feature flag first.** Don't attempt any of the steps
   below until the user confirms both that they're on a Voxel51 deployment and
   that remote agent access is enabled for it. If they're not sure, tell them to ask
   their FiftyOne admin.
2. **Always use the user's own deployment URLs.** Never invent, assume, or reuse a
   URL from an example, docs page, or a different deployment. Ask for them if not
   given.
3. **Never ask the user to paste, type, or store an access token by hand.** Both
   connection paths below handle credential storage automatically and safely
   (`~/.fiftyone/agent.json`, file mode `0600`, for the CLI path). If you find
   yourself about to ask for a raw key or token, stop, that's the wrong step.
4. **A one-time browser approval is required and cannot be skipped.** Both the CLI's
   device-flow login and an MCP client's OAuth connection need a human to sign in and
   click Approve in a browser. Tell the user to expect this, then wait for it, don't
   suggest a way around it.
5. **Treat a permission refusal as expected behavior, not a bug.** If an operator is
   missing from the list, or a pairing attempt is refused because the approving user
   lacks a specific permission, that's the live permission check working correctly,
   see Troubleshooting. Never suggest disabling, bypassing, or "working around" a
   refusal.
6. **Prefer MCP for editor-native agents** (Claude Code, Cursor, any MCP client) and
   **the CLI for scripts or headless shells.** Both reach the same operators with the
   same permissions; the choice is about the environment, not the capability.
7. **New MCP servers only attach on the next session.** After adding one, tell the
   user plainly they need to restart their agent (or start a fresh conversation)
   before the tools are usable; it will not work in the current turn.
8. **Consult `references/` before guessing at an operator or its arguments.** Don't
   invent an operator URI or parameter shape from general FiftyOne knowledge or a
   past conversation — different deployments have different plugins installed and
   different schemas. Read the matching category file under `references/` first,
   then confirm the exact current arguments with `get_operator_schema` before
   calling `execute_operator`. See "Using the tools well" below.

## Prerequisites

- A Voxel51 deployment with remote agent access enabled by an admin.
- The deployment's gateway URL (for MCP:
  `https://<your-deployment>/api/proxy/fiftyone-teams/mcp`; for the CLI: an API base
  URL, `https://<your-deployment>/api/proxy/fiftyone-teams`, and an auth base URL,
  `https://<your-deployment>/cas/api`). Get the deployment hostname from the user or
  their FiftyOne admin, don't guess it, but these path suffixes are fixed.
- To use the CLI path: a `fiftyone` install that includes the `agent` command group
  (`fiftyone agent --help` should list `login`, `status`, `logout`, `operators`).
- To use the MCP path: an MCP client that supports remote HTTP servers with OAuth
  (Claude Code, Cursor, and similar all do).

## Workflow

### Path A: Connect via MCP (Claude Code, Cursor, any MCP client)

1. Ask the user for their deployment's agent gateway URL if not already given:
   `https://<your-deployment>/api/proxy/fiftyone-teams/mcp`.
2. Add it as a remote MCP server. In Claude Code:
   ```
   claude mcp add --transport http --scope user voxel51-agent-gateway \
     https://<your-deployment>/api/proxy/fiftyone-teams/mcp \
     --client-id voxel51-agent-mcp
   ```
   The `--client-id` is required: this deployment's auth server doesn't support
   Dynamic Client Registration, so a client that tries to register one on its own
   fails with `Incompatible auth server: does not support dynamic client
   registration`. `voxel51-agent-mcp` is the fixed client id every agent uses.
   Only run this after the user confirms; it edits their global agent config. For
   other clients, give the equivalent config snippet, e.g. Claude Desktop / Cursor:
   ```json
   {
     "mcpServers": {
       "voxel51-agent-gateway": {
         "type": "http",
         "url": "https://<your-deployment>/api/proxy/fiftyone-teams/mcp"
       }
     }
   }
   ```
   If the client's config format has no explicit way to pin a client id and it
   fails the same DCR error above, that client isn't yet supported for this path;
   fall back to the CLI (Path B) instead.
3. Tell the user to restart their agent (per Key Directive 7), then trigger the
   connection (e.g. by trying to use one of the new tools). Their agent will open a
   browser for a one-time OAuth consent screen, they sign in and approve, and the
   connection is complete, no API key needed.
4. Once connected, five tools are available: `list_operators`, `get_operator_schema`,
   `execute_operator`, `list_delegated_operations`, `get_delegated_operation` — covering
   whatever FiftyOne operators the approving user's account is permitted to see and run,
   live-checked on every call. Long-running operators can be run in the background with
   `execute_operator(..., delegate=True)`; check the result's `delegated` field (not every
   operator supports it) and poll `get_delegated_operation` for the outcome.

### Path B: Connect via the `fiftyone` CLI

1. Ask the user for their deployment's API base URL and auth base URL if not already
   given.
2. Run the login flow:
   ```
   fiftyone agent login --api-url https://<your-deployment>/api/proxy/fiftyone-teams --auth-url https://<your-deployment>/cas/api
   ```
3. This prints a short code and a URL. Tell the user to open the URL in a browser
   (already signed in to their FiftyOne account) and approve the pairing there. The
   command waits and prints "Connected" once approved.
4. From then on:
   - `fiftyone agent status` — show what's paired and its scope/expiry.
   - `fiftyone agent operators list` (add `--json` for machine-readable output) —
     list operators the paired account can currently run.
   - `fiftyone agent operators run <uri> --params '{"key": "value"}'` — run one. Add
     `--delegate` for long-running operators; check the printed `delegated` value (not
     every operator supports it) and follow up with `status` below.
   - `fiftyone agent operators status <operation-id>` — check on a delegated run.
   - `fiftyone agent operators list-delegated` — list your own delegated operations.
   - `fiftyone agent logout` — remove the stored credential from this machine.

## Using the tools well

The MCP path's five tools (`list_operators`, `get_operator_schema`, `execute_operator`,
`list_delegated_operations`, `get_delegated_operation`) and the CLI's `agent operators`
commands are generic — they reach whatever FiftyOne operator you name. The operator
catalog behind them is large (typically hundreds, varying by deployment and the
connected user's own permissions), and most individual operators carry no written
description of their own. Don't call `list_operators` cold and scan every name, and
don't guess at an operator's purpose or arguments from memory.

Instead:

1. **Start from `references/`, not from `list_operators`.** Read the one file that
   matches the current task:
   - [`references/datasets-and-samples.md`](references/datasets-and-samples.md) —
     dataset lifecycle, views, fields/schema, sample and label edits, indexes,
     media import, workspaces.
   - [`references/analysis-and-labeling.md`](references/analysis-and-labeling.md) —
     brain methods, embeddings, model evaluation, data quality, auto-labeling,
     agentic labeling, annotation, zoo models, workflows, label schemas.
   - [`references/delegated-operations.md`](references/delegated-operations.md) —
     running things in the background, checking on them, delegated-run metadata.
   - [`references/agent-tools.md`](references/agent-tools.md) — the FiftyOne Agent's
     own operators (conversations, code execution, plugin/skill authoring, memory).
   - [`references/not-available.md`](references/not-available.md) — real,
     commonly-requested things that **aren't** reachable this way today, and why.
     Check this before spending calls discovering it the hard way.
2. **Treat the reference files as a map, not a schema.** They name real operator URIs
   and what each is for; they deliberately don't restate exact parameters, because
   those can differ by deployment, dataset, and plugin version. Always call
   `get_operator_schema` for the operator you've settled on before calling
   `execute_operator` with anything beyond no/trivial parameters.
3. **`list_operators(dataset_name=...)` is live-permission-filtered.** Use it to
   confirm an operator a reference file names is actually available to this caller
   on this dataset, not to browse — it returns bare URIs with no description.
4. **Delegate long-running work.** `execute_operator(..., delegate=True)` queues a
   background run instead of blocking; check the response's `delegated` field (not
   every operator supports it), then follow up per
   [`references/delegated-operations.md`](references/delegated-operations.md).

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `Incompatible auth server: does not support dynamic client registration` when adding or logging in to the MCP server | The MCP client tried to self-register a client id; this deployment's auth server doesn't support that | Remove and re-add the server with an explicit `--client-id voxel51-agent-mcp` (see Path A step 2) |
| `NotPairedError` on any `agent operators` command | Never logged in on this machine, or logged out | Run `fiftyone agent login` first |
| Pairing approval is refused, mentions a missing permission | The signed-in user approving the pairing doesn't have the `USE_API_KEYS` permission on their account | Ask a FiftyOne admin to grant that permission to the user's account, this is intentional, not a bug |
| An operator you expect isn't in `list_operators` / `agent operators list` | The connected account's current role or dataset permissions don't allow it | Working as intended, permissions are re-checked live on every call, not cached. Confirm with the account's admin what it should have access to |
| Everything worked, then started failing after a while with an auth error | The access token (short-lived, ~1 hour) expired and the automatic refresh also failed, most likely the pairing was revoked | Re-run `fiftyone agent login`, or reconnect the MCP server |
| MCP tools don't appear right after adding the server | New MCP servers only attach on the next session (Key Directive 7) | Restart the agent / start a fresh conversation |
| User is on OSS FiftyOne, not Voxel51 | This whole feature is Voxel51-only | Point them at the local `fiftyone-mcp` server instead, which needs no pairing |

## Resources

- [Voxel51 documentation](https://docs.voxel51.com/enterprise/index.html)
- [FiftyOne CLI documentation](https://docs.voxel51.com/cli/index.html)

# Set Up an Agent for Voxel51

Pair a local agent (Claude Code, Cursor, any MCP client) or the `fiftyone` CLI to a
Voxel51 deployment, acting with your own account's permissions.

## Install

```bash
curl -sL skil.sh | sh -s -- voxel51/fiftyone-skills
```

When prompted, select **voxel51-agent-setup** from the menu.

## Requirements

- [Voxel51](https://docs.voxel51.com/enterprise/index.html) with remote
  agent access enabled by an admin (Voxel51-only, off by default)
- Your deployment's gateway URL(s), from your FiftyOne admin
- An MCP-compliant client (Claude Code, Cursor, etc.) for MCP, or a `fiftyone` install
  with the `agent` CLI commands for the CLI path

## Usage

Ask your AI assistant:

```
"Connect my agent to our Voxel51 deployment"
"Pair Claude Code with Voxel51"
"Set up fiftyone agent login for our deployment"
```

Provide your deployment's URL(s) when asked, and the skill walks you through either
adding it as a remote MCP server or running `fiftyone agent login`, then a one-time
browser approval completes the pairing.

## Note

> Remote agent access is a Voxel51 feature and must be explicitly enabled
> by the deployment's administrator. It won't work on open-source FiftyOne, or on a
> Voxel51 deployment where it hasn't been turned on.

## See also

- [Voxel51 docs](https://docs.voxel51.com/enterprise/index.html)
- [FiftyOne CLI docs](https://docs.voxel51.com/cli/index.html)

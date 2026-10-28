# Not available through this gateway today

Check here before spending several calls discovering one of these the hard way.
None of these are a sign of a misconfigured connection or a missing permission —
they're real gaps, worth naming plainly to the user rather than working around.

## Generic field aggregations
There's no operator for a plain "count values of this field," "distinct values,"
"histogram," or "mean/sum/std/bounds of this field" query. The only way to answer
that kind of question through this gateway today is writing and running Python via
`@voxel51/fiftyone-agent/execute_code` — heavier and riskier than a dedicated
aggregation call would be. If a user asks something like "what's the distribution of
labels in this field," say plainly that there's no direct tool for it yet and offer
`execute_code` as the fallback, rather than searching for a tool that doesn't exist.

## Dataset-wide summary
Same story — no operator bundles "schema + sample count + per-field value counts" in
one call the way some local tools do. Build the picture from
`@voxel51/operators/get_field_schema` plus individual queries, or `execute_code`.

## Voxel51 administration
None of the following are operators — they're REST/GraphQL-only on the platform
side, with no path into this gateway at all:
- Users, roles, groups, API keys (RBAC)
- Dataset snapshots (versioning, revert)
- Secrets management
- Orchestrator/compute-pool registration (as opposed to day-to-day use of an
  already-registered one, which does work — see
  [`analysis-and-labeling.md`](analysis-and-labeling.md))
- SSO / identity provider configuration
- The org-wide audit log
- Billing, usage, seats
- LLM/model connection configuration
- Org-wide settings, cloud storage credentials, event archival
- Uploading, upgrading, or updating a plugin (installing/enabling/disabling an
  already-published one does work — see
  [`datasets-and-samples.md`](datasets-and-samples.md))
- Admin actions on a delegated operation (rerun, archive, pin, relabel, force-fail)

If a user asks for any of these, say so directly and point them at the App's own
Settings/admin pages rather than attempting it through the agent.

## Live App-session actions
Pushing a view to an open App tab, opening or closing a panel, toggling the
sidebar, reading what's currently selected, or launching a new App instance all
require one live, connected browser session to mean anything. This gateway is a
stateless server handling concurrent requests from many users — there is no
"current" anything for it to act on. This is architectural, not a missing feature;
it won't become possible by finding the right operator name.

## The in-app Agent's internal memory and `Skill` meta-tool
The in-app Voxel51 Agent has its own three-tier memory system and a `Skill`
invocation mechanism, both hardcoded into its own LLM loop rather than implemented
as FiftyOne operators. Nothing reachable through this gateway touches either one.

# Datasets & samples

The core SDK surface — dataset state, no live App session required. Call
`list_operators(query=...)` to find the current operator for what you need —
try keywords like "create dataset", "saved view", "field schema", "clone
field", "create index", "import media", or "workspace". It's live,
permission-filtered, ranked, and already includes each result's description,
so a maintained inventory here would only go stale (the old one already had).
Confirm exact arguments with `get_operator_schema` before calling any of them.

## Known gotchas not visible from a search result or schema alone

`manage_indexes` has a dynamic form — a call naming no field to create or drop
returns the operator's own "nothing to do" notice rather than an error. Name a
real field (confirm with `get_field_schema` first) to get a useful result.

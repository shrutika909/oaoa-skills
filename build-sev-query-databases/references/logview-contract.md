# LogView replay contract

## Discovery

Resolve LogView evidence from OpsMate trajectory calls and incident artifacts.
Recognize context names, 32-character MIDs, LogView URLs, health-incident IDs,
sample keys, sample tabs, and explicit query windows. Do not assume a fixed
context or schema.

Use the production read surfaces corresponding to:

- context discovery and description
- MID search/list, schema, lookup, metadata, trend, and triage
- sample-tab and sample-key lists
- sample schema and selected sample content
- thread list/read
- selected sample metadata key list/read

Record the command shape, context, MID, sample key or tab, constraints, start,
end, cutoff, result hash, and row count in the private inventory.

## SQLite model

Materialize each selected operation as a registered `query_catalog` entry and
one operation-specific table. Store `operation`, `context`, native column
metadata, supported filters, time bounds, and privacy capability in
`metadata_json`.

Supported operation names:

- `context_describe`
- `mid_list`
- `mid_metadata`
- `mid_trend`
- `mid_triage`
- `sample_list`
- `sample_thread_list`
- `sample_thread_read`
- `sample_metadata_read`

Preserve MID-to-sample-to-thread relationships, trend bucket ordering,
occurrence counts, triage dimensions, missing values, empty results, pagination
boundaries, and cutoff behavior.

## Privacy

Treat metadata values as sensitive unless explicitly reviewed. Thread callstack
structure may be staged when the source interface exposes it without sensitive
authorization, but still pseudonymize repository-specific identifiers when the
task leaves Meta.

Never export:

- Metamate API keys or other credentials
- raw sensitive-mode responses
- device serials or direct user/account identifiers
- raw request or POST bodies
- unbounded logcat
- private ToolReceipts or source-to-replay mappings

For `sample_metadata_read`, require `privacy.values_approved=true` and an
explicit `privacy.included_keys` list. Preserve denied/redacted behavior so the
offline agent cannot infer that unavailable data would have answered the task.

## Replay behavior

Expose only registered operations through the loopback replay service. Allow
bounded time windows, limits, and exact-match filters on declared columns.
Reject unknown operations, unknown columns, out-of-snapshot windows, excessive
limits, malformed requests, missing authorization, and non-positive timeouts.
Write a private receipt for each success, empty result, denial, failure, limit,
and timeout.

`task/contracts/logview.json` defines every bounded operation the adapter can
serve. `query_catalog` lists which LogView operations and query IDs are
materialized for the task.

## Validation

Validate schema capture, row counts, relationship preservation, deterministic
rebuild, cutoff enforcement, exact filters, empty/error behavior, privacy
rejection, private receipt isolation, and access from the separate task
container. Compare replayed operation results with bounded approved source
receipts, not with live production after the cutoff.

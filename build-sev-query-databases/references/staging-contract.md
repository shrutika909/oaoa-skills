# Staging contract

The authoring agent automatically discovers evidence from the requested SEV and
writes this bounded staging format. The executable scaffolder never contacts
production and cannot silently backfill missing data.

```
<staging>/
  trajectories/*.json
  sources/*.json
```

## Trajectory file

Provide a stable `trajectory_id` or `session_id`, `harness`, `cutoff`, and an
`events`, `steps`, or `messages` array. An event identifies its tool with
`tool`, `tool_name`, or `name`; supplies `request`, `input`, or `arguments`; and
may include `timestamp`, `operation`, and `status`.

## Query-source file

Required fields:

- `sev_id`
- `tool`: `scuba`, `hive`, `daiquery`, `presto`, or `logview`
- `query_id`, unique within the tool
- `source_lineage_id`, an opaque build-scoped identifier for one distinct
  production dataset, table, relation, or LogView resource family
- `resource_name`
- `columns`: ordered objects with `name` and native `type`
- `rows`: objects keyed by column name
- `classification` and private `classification_reason`
- `time_range`, including the evidence cutoff
- `invariants` that must remain true after transformation
- `volume`, following `scale-contract.md`, including profile, scale basis,
  source/materialized row and byte measurements, sampling, and preserved
  distributions

Optional fields include `query`, `identity`, and `supported_functions`.
Classification and reasoning remain private; the scaffolder writes neither to
SQLite nor to the agent-visible package.

Export-mode sources must also contain:

```json
{"anonymization":{"strategy":"synthetic_reconstruction","release_eligible":true}}
```

The executable scaffolder rejects pseudonymized or unmarked sources in export
mode. Generate the marker only through the approved reconstruction flow.

Duplicate files are skipped by content hash. A source for another SEV or an
unsupported tool is skipped and recorded in the private build report.

Distinct source lineage IDs must remain distinct fictional resources and
tool-specific tables. Two production datasets may not be normalized into one
generic task dataset, even when they share columns or participate in one causal
chain. One lineage also may not fan out into multiple fictional resources.
Synthetic resource names must differ from production names.

The author-facing scaffold groups private classifications into an evidence
mix: `bullseye` is `causal`; `directional` remains separate; and `misleading`
is the sum of `competing` and `negative`. Report both source counts and row
counts. These labels and counts remain private and must not enter the task
prompt, agent package, public README, CLI output, or replay responses.

Difficulty may be increased with additional `competing` or `negative` evidence
only when it is realistic, provenance-backed, and falsifiable using visible
evidence. Never add arbitrary noise, false facts, or an unfalsifiable decoy.
Re-run independent-solvability and decoy-falsifiability checks after changing
the mix.

Source-count floors prevent a single clue from masquerading as diversity, but
they do not establish realistic scale. Apply them together with the row-share
and byte requirements in `scale-contract.md`:

| Role | Minimum synthetic records |
|---|---:|
| Bullseye / causal | 4 |
| Supporting | 4 |
| Directional | 4 |
| Misleading / competing | 6 |

Do not treat a few dozen records as a dense profile. Completed database tasks
retain at least 500 MB, with row count determined by the source population and
row width rather than an arbitrary millions-of-rows target.
When approved source material cannot support production-like volume, preserve
fidelity and block the database path instead of padding or publishing a toy
dataset.

The floors are not row-duplication targets. A hardening set must contain at
least three plausible competing hypotheses. Each hypothesis needs at least two
independent clues and at least one agent-visible falsifier. Spread evidence
across at least two of: source resource, tool surface, scope, or time segment.
Misleading records should be at least as numerous as bullseye records but no
more than three times as numerous; outside that band, document why the task
remains independently solvable. Repeated rows, cosmetic renames, and several
records that all expose the same inference count as one clue.

## LogView source requirements

Each LogView source also declares `operation`, one of `context_describe`,
`mid_list`, `mid_metadata`, `mid_trend`, `mid_triage`, `sample_list`,
`sample_thread_list`, `sample_thread_read`, or `sample_metadata_read`.
Include `context` and the context-specific schema. Sample metadata sources must
set `privacy.values_approved=true` and list `privacy.included_keys`; otherwise
the executable scaffolder rejects them. Never stage an API key, device serial,
credential, raw request body, or unreviewed sensitive-mode response.

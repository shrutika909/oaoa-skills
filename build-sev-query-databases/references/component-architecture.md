# Component architecture

Keep orchestration small. Production authoring is a staged pipeline with
independent, fail-closed components.

| Stage | Component | Responsibility |
|---|---|---|
| 0 | `sev_context` | Resolve canonical SEV row, cutoff, owner, owner oncall rotations, alerts, SLIs, investigation range, and source gaps. |
| 1 | `experiment_discovery` | Resolve live OAOA arms, registered Ent experiments, sessions, harness identity, and trajectory readability. |
| 2 | `reference_extraction` | Extract typed Scuba, ODS, Hive, Presto, dashboard, notebook, and saved-query references from SEV text and trajectories. |
| 3 | tool collectors | Independently resolve metadata and bounded historical results for one tool family. |
| 4 | normalization | Produce the common private event/source envelopes without changing meaning. |
| 5 | selection | Privately classify causal, supporting, directional, negative, competing, duplicate, inaccessible, and excluded sources. |
| 6 | materialization | Build SQLite, SQL dump, replay service, clients, docs, and manifests from approved staging only. |
| 7 | validation | Run reconstruction, interface, behavior, leakage, determinism, isolation, receipt, and size checks. |

## Upstream tools

- `sev-to-json` is the deterministic raw SEV intake pattern.
- `sev-evidence-pack` is the canonical author-only evidence and reference
  pattern: isolated collectors, command allowlist, source gaps, artifact hashes,
  staged execution, and private storage.
- `ods-tool` is the native-tool materialization pattern: plan from the SEV,
  stage real data, deterministic fill, replay service, receipts, and self-test.
- `incident-evidence-kit` defines the public/private/audit trust boundary.

Do not duplicate those responsibilities in one script. When an installed
`sev-evidence-pack` is available, consume its telemetry-reference items rather
than re-scraping prose. The database skill owns the stage-3 Scuba, ODS,
Daiquery/Hive, and Presto data collectors.

## Oncall-to-table discovery

The SEV's `owner_oncall_rotations` is a discovery namespace, not permission to
copy every table owned by that oncall. Build the candidate union from:

1. alert queries, linked SLIs, dashboards, and relevant-metrics links
2. every database call in all discovered trajectories
3. typed telemetry references from `sev-evidence-pack`
4. oncall-owned catalog assets related to the affected services and symbols

Record all candidates. Include only bounded sources that are relevant to the
SEV or a realistic investigation path. Record duplicate, unrelated, denied,
unsupported, post-cutoff, and excluded oncall assets in the private manifest.
Never silently expand from one oncall to its entire warehouse footprint.

Every component writes a result envelope with `status`, `commands`, `items`,
`gaps`, timestamps, and input hashes. Later stages may continue after an
optional component fails, but production materialization is blocked whenever a
required channel is incomplete.

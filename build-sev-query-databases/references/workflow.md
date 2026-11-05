# Workflow

## 0. Clear the cross-author registry gate

Normalize the requested SEV ID, then run the mandatory registry procedure in
`SKILL.md` before reading private incident material. The evidence must combine:

- a complete, successful exact-SEV search in the active cross-author OAOA Task
  Registry
- current repository and all branch-tip exact-SEV searches
- bounded commit metadata/history and active-session searches
- the Knots authoring-claim state supplied by the parent autopilot

Record the result in an author-only receipt. Stop if any surface is incomplete
or ambiguous, or if any current or historical task/claim matches the SEV. The
registry UI excludes archived tasks and therefore cannot be the only duplicate
check. Do not open trajectories or production query results until this phase
passes.

## 1. Resolve the investigation

Load the SEV, then automatically discover its linked OpsMate experiments, every
relevant custom arm and trajectory, and cutoff data. Do not require trajectory
URLs as input and do not hardcode a fixed number of trajectories. Use stable
IDs. Record the retrieval method and timestamp without copying raw narratives
into exported artifacts.

Inspect the SEV stakeholder tool-activity dataset as one discovery source:
`sevmate_sev_stakeholders_intern_tool_activity`. Also inspect linked alerts,
runbooks, investigation artifacts, and relevant trajectories. Determine and
record the required baseline, incident, and recovery time ranges plus the
evidence cutoff. Treat an optional supplied query list as seeds to verify and
expand, not as complete evidence.

## 2. Normalize trajectory events

Convert harness-specific records from Muse, MetaCode, Claude, Codex, and other
supported harnesses into one private event envelope:

`trajectory_id`, `harness`, `timestamp`, `tool`, `operation`, `request_ref`,
`response_ref`, `status`, `cutoff`, and `provenance`.

Preserve attempted, failed, retried, abandoned, and successful database calls.
Normalization changes representation, not meaning.

## 3. Discover database evidence

Start from trajectory calls, then inspect approved SEV artifacts for additional
queries needed to make the task realistic and independently solvable. Consider
Scuba, Daiquery, Hive, Presto, and LogView. Use enough sources to cover the required
evidence; do not ingest every source. Skip duplicates and record why each source
was used or skipped. Include only tools used by a relevant discovered trajectory
or an approved production investigation path.

Classify each candidate privately as `causal`, `supporting`, `negative`,
`competing`, or `excluded`. Record the reason and provenance. Include enough
needed and realistic unwanted evidence for the task to be solvable without
giving away the answer. Do not add arbitrary noise or disclose which evidence
is decisive.

Build a private scale plan from observed row/byte counts, frequency
distributions, missingness, skew, and time density. Derive materialized row
count from the original population and retain at least 500 MB. Bullseye rows
should be rare; preserve the larger background
and competing population so full-table inspection is not a shortcut.

## 4. Human review gate

Present a short proposed inventory containing:

- trajectories and cutoffs
- tools and query families
- evidence counts by private class
- author-only evidence-mix counts by sources and rows: bullseye (`causal`),
  supporting, directional, misleading (`competing` plus `negative`), and
  excluded
- planned transformations
- exclusions and unresolved gaps
- expected package size

Do not materialize anything until the human explicitly approves this inventory.

If difficulty needs to increase, prefer realistic, provenance-backed competing
or negative evidence that the visible replay can falsify. Do not add arbitrary
noise or false facts, and never weaken independent solvability.

Hardening changes inference structure, not just volume. Apply the density and
hypothesis rules in `staging-contract.md`: several distinct competing
hypotheses, multiple clues per hypothesis, and a visible falsifier for each.
Measure the resulting mix again after every calibration-driven change.

Audit every calibration trajectory for reward hacking: private-path access,
answer leakage, fabricated evidence identifiers, report-template copying,
grader/parser exploitation, citations without observation, raw database access,
or scoring without the required investigation and recovery sequence. A
reproduced exploit becomes a permanent negative control before publication.

## 5. Transform deterministically

Apply one shared identifier and time mapping across all included tools. Preserve
joins, ordering, cardinality relationships, error semantics, causal signals,
and diagnostic invariants. Reject transformations that cannot preserve them.
Do not synthesize rows with a language model.

Produce tool-specific metadata alongside the data: visible resources, fields,
types, descriptions, supported query/counter functions, time semantics,
identity requirements, and schema-discovery behavior. Do not copy ODS schema
terminology into Scuba or Hive when their native concepts differ.

## 6. Build the component

Create one SQLite database per generated task, derived from one SEV. Use
tool-specific tables or views and read-only adapters. Include only the tools
selected in phase 3. Keep the database budget at or below 3 GB and the complete
component package at or below 4 GB.

Measure source and destination row counts and byte sizes for every conversion.
These are audit measurements, not quotas. Never remove evidence required to
preserve the answer or legitimate alternate investigations merely to reduce a
count. If required evidence cannot fit, mark the build blocked.

Do not over-normalize. Preserve distinct lineages, native-width fields,
repeated events, retries, duplicates, sparse values, partition structure, and
distribution shape when diagnostically relevant. Summaries may accompany
detail rows but may not replace the realistic detail population.

The task container receives tool-specific CLIs. A separate replay container
owns `scenario.sqlite`, the adapters, and private receipts. Adapters accept the
native tool request shape and return native-looking results; they do not expose
raw SQL or filesystem access.

On Linux, run both containers with host networking and bind the replay service
only to `127.0.0.1`; never bind it to `0.0.0.0`. Store receipts in a
container-owned named volume. Do not mount the private authoring directory into
either container. Validate access from a second container, not only from the
replay container itself.

Generate a deterministic `scenario.sql` dump and verify it reconstructs the
same database. Generate a shell script that starts the small replay service in
the replay container; SQLite remains embedded and is not itself a server.
Generate a Bash CLI wrapper plus an executable Python client that connects only
to the replay service, with a client startup script. The implementation language
for adapter internals is selected explicitly in the component manifest rather
than left as an unspecified “X programming language.”

Treat LogView as a first-class operational source. Discover it from trajectory
calls, LogView URLs, health incidents, MIDs, context names, and sample keys.
Preserve only the surfaces used by the investigation: context metadata, MID
lists and metadata, occurrence trends, triage distributions, sample tabs and
keys, thread structure and frames, or selected metadata keys. Record the source
command shape and cutoff for each surface.

LogView schemas vary by context. Capture both MID and sample schemas before
data. Keep public call stacks structurally faithful. Treat sample metadata
values as sensitive by default: stage only approved keys, remove credentials
and direct identifiers, and keep the source-to-replay mapping private. Never
copy Metamate API keys, raw sensitive-mode responses, device serials, request
bodies, or other UII into the agent-visible package. Preserve redaction and
authorization failure behavior in replay.

## 7. Document and validate

Generate man pages for each included adapter and a README quick start. Validate:

1. fidelity against approved source receipts
2. privacy and answer leakage
3. deterministic rebuilds
4. offline isolation
5. native CLI behavior and errors
6. independent solvability by an evaluator without private artifacts

Record every replay invocation in a private ToolReceipt, including successes,
failures, denials, retries, limits, and timeouts. The solving agent cannot read
or forge receipts.

Write the output artifacts defined in `output-contract.md` even when validation
fails, marking the overall status `blocked` and listing failures. Runtime has no
deadline. Record phase start, end, and elapsed time for diagnosis only.

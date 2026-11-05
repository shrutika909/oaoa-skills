# Database scaffolding build report

## Identity

- SEV:
- Run ID:
- Status:
- Started/finished:
- Total elapsed time:

## Phase timing

For each phase record start time, end time, elapsed time, and status. Timing is
diagnostic and has no pass/fail limit.

## Source ledger

List automatically discovered experiments, custom trajectory IDs, harnesses,
cutoffs, retrieval methods, and hashes. Do not copy raw sensitive content into
this report.

Record the SEV tool-activity lookup, supplied query seeds, discovered queries,
and the baseline, incident, recovery, and cutoff time ranges.

## Source decisions

List sources used and skipped. Record duplicate, irrelevant, inaccessible, and
post-cutoff reasons.

## Discovery ledger

List targeted query families, private evidence classifications and reasoning,
provenance, exclusions, and unresolved gaps.

## Transformation ledger

For every conversion, list deterministic mappings, source and SQLite objects,
row counts, byte sizes, and diagnostic invariants checked. Counts and sizes are
measurements, not quotas.

## Scale profile

Record the 500 MB floor, actual database bytes, total rows, source rows/bytes,
per-resource rows/bytes, sampling, preserved distributions, evidence-role row
shares, the source-derived row-count rationale, and whether the floor passed. A tiny contract fixture
must never be reported as a completed production-scale database.

## Component ledger

List SQLite namespaces, adapters, CLIs, man pages, container files, versions,
sizes, and hashes. Mark each component created, reused, skipped, or failed.
Include `replay/scenario.sqlite`, the reconstructable `replay/scenario.sql` dump, replay and
client startup scripts, Bash CLI, executable Python client, ToolReceipt sink,
and Longview representation status.

## Validation ledger

Record fidelity, leakage, determinism, isolation, native behavior, and
independent-solvability results.

## Provenance binding

Record the source-inventory and synthetic-specification hashes.

## Failures and follow-ups

Record retries, unresolved gaps, blockers, owners, and exact next actions.

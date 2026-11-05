# Output contract

## Replay package

- `replay/scenario.sqlite`: one read-only SQLite file for the task
- `replay/scenario.sql`: deterministic SQLite dump
- `replay/contracts/`: server-side copies of the five ToolSpecs
- `replay/scripts/start-replay.sh`: start the isolated replay service

## Task package

- `task/contracts/`: versioned Scuba, Daiquery, Hive, Presto, and LogView ToolSpecs
- `task/bin/`: five named read-only CLIs plus the Python client
- `scripts/start-client.sh`: initialize the client without exposing the database
- `man/`: one man page per included tool
- `README.md`: startup and usage instructions
- `component_manifest.json`: versions, files, sizes, hashes, and interfaces
- `validation_report.json`: validation checks and status
- `checksums.sha256`: integrity hashes
- `scaffolding_summary.json`: machine-readable handoff to the parent scaffolder

The solving agent must not receive direct database access, private manifests,
receipts, transformation maps, answer labels, or build reasoning.

## Private authoring package

- `private/private_authoring_manifest.json`: trajectories, query targets,
  evidence classes, hidden evidence, exclusions, coverage gaps, provenance, and
  artifact references
- `private/build_report.md`: private phase ledger defined below
- `private/test_report.md`: exact commands, expected/actual status, evidence, and verdict
- `private/anonymization_mapping.md`: exact identifier replacements, shared time
  shift, preserved value classes, and re-identification review notes
- `private/database_mapping.md`: source tool/resource/query to SQLite table,
  column, type-metadata, row-count, and replay-interface mappings
- `private/receipts/`: approved source hashes and bounded comparison records
- `private/transforms/`: deterministic identifier/time mappings

## Summary requirements

`scaffolding_summary.json` must state the SEV, selected trajectories, included
tools, database path and size, adapter interfaces, validation status, known
gaps, release mode, export eligibility, and the exact files the parent
scaffolder should consume. It also includes the private `evidence_mix`, with
exact source and row counts for bullseye, supporting, directional, misleading,
and excluded evidence. The parent must keep this field author-only.

It also includes `scale_profile`: target and actual database bytes, total
materialized rows, source rows and bytes, per-tool/resource row and byte counts,
sampling strategy, preserved distributions, role row shares, and booleans for
the 500 MB completion floor and source-derived row-count check. A real export below the floor is
blocked; `contract_fixture` is test-only and never release eligible.

For an explicitly hardened task, the same private authoring document records
whether the density floors, misleading-to-bullseye ratio, competing-hypothesis
count, clue independence, surface diversity, and visible-falsifier checks pass.
Counts alone never establish difficulty.

## Private build report requirements

`private/build_report.md` is visible to authors and evaluators only. Never copy
it into the agent container, task prompt, public README, man pages, or
agent-visible package.

It must contain:

1. Run identity, status, phase start/end timestamps, elapsed time, and total time
2. Automatically discovered experiments, custom trajectories, harnesses, and cutoffs
3. Sources used and skipped, including duplicate, irrelevant, inaccessible, and post-cutoff reasons
4. Targeted query families and private evidence classification with reasoning,
   plus exact bullseye, supporting, directional, misleading, and excluded
   source and row counts
5. Source-to-SQLite mapping for every conversion
6. Source and destination row counts and byte sizes as measurements
7. Components created, reused, skipped, or failed, with versions and hashes
8. Validation results for fidelity, leakage, determinism, isolation, native behavior, and solvability
9. Failures, retries, unresolved gaps, and follow-ups

There is no build-time limit. Size limits are 3 GB for `scenario.sqlite` and
4 GB for the complete component. Necessary causal and alternate-path evidence
must remain present.

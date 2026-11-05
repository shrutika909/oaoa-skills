## 11. V1 scaffolding observability and database build report

This section records the V1 decisions for the query-database component. Where
earlier text describes Parquet and DuckDB as the MVP storage engine, this
section supersedes it for V1: create one shared SQLite database per task/SEV.
DuckDB and Parquet are deferred until measured SQLite size or performance
limits require them. SQLite is embedded; a small replay service may expose it
inside the separate replay container, but SQLite itself does not require a
database server.

### Automatic evidence discovery

The skill takes a SEV as its required input. It automatically discovers linked
OpsMate experiments, relevant custom arms and trajectories, their harnesses,
and cutoffs. Trajectory URLs and a fixed number of trajectories are not skill
inputs and must not be hardcoded. Harness-specific Muse, MetaCode, Claude,
Codex, and other supported records are normalized into one private event model
before query evidence is selected.

The skill does not ingest every available source. It uses enough non-duplicate
evidence to preserve the causal answer, legitimate alternate investigations,
healthy and incident context, meaningful negative evidence, and realistic
unwanted or misleading evidence. It records every used source and each skipped
source with a reason such as duplicate, irrelevant, inaccessible, or
post-cutoff. Necessary evidence must not be removed merely to reduce size.

### Limits and measurements

The V1 limit is 3 GB for `scenario.sqlite` and approximately 4 GB for the
complete component package. If required evidence cannot fit, the build fails
with a size report instead of silently removing the answer or an approved
alternate path.

For every source-to-SQLite conversion, record source and destination row counts
and byte sizes. These values are audit measurements, not quotas. The build has
no runtime deadline. Record timing to diagnose slow phases and improve the
scaffolder, not to accept or reject a task.

### Private `build_report.md`

Every run writes `private/build_report.md` in authoring/verifier storage. The
task-solving agent must not receive this file or any equivalent private fields.
The report contains:

1. Run identity, overall status, phase start/end timestamps, elapsed time, and total time.
2. Discovered experiments, custom trajectories, harnesses, cutoffs, and retrieval methods.
3. Sources used and skipped, with deduplication and exclusion reasons.
4. Targeted query families and private causal, supporting/directional, negative, competing/misleading, or excluded classifications with reasoning.
5. Every source-to-SQLite table/view transformation and the invariants preserved.
6. Source and destination row counts and byte sizes.
7. Components created, reused, skipped, or failed, including SQLite objects, adapters, CLIs, replay-container files, man pages, versions, sizes, and hashes.
8. Fidelity, privacy/leakage, determinism, offline isolation, native behavior, and independent-solvability results.
9. Failures, retries, unresolved gaps, blockers, ownership, and follow-up actions.

The agent-visible scaffolding summary contains only safe component status,
interfaces, versions, sizes, and validation outcomes. It excludes query labels,
classification reasoning, hidden evidence, reversible mappings, source paths,
receipts, and benchmark conclusions.

### API compatibility documentation

Maintain a one-time design comparison for each adapter describing the real
tool behavior preserved by the simulated CLI, intentional V1 omissions, and
any open-source interface used as a design reference. This is a design-review
artifact, not a per-SEV build step and not a requirement to imitate an
open-source tool.

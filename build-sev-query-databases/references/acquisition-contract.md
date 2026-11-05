# Production acquisition contract

Production discovery runs only in an authenticated internal authoring
environment. The executable scaffolder never queries production.

1. Resolve the SEV and its incident artifact ID and time bounds.
   Capture the canonical owner, owner oncall rotations, linked alerts, linked
   SLIs, affected services, and investigation window. Use oncall ownership to
   expand candidate discovery, not as an instruction to ingest every owned
   table.
2. Discover the current OAOA OpsMate experiment registry automatically. Never
   require an experiment ID from the caller and never embed a frozen ID list.
3. Export runs for every registered experiment and select rows by the resolved
   incident artifact ID; use the normalized SEV short name only as a checked
   fallback. Preserve experiment, arm, role, AgentRef/harness, execution ref,
   trajectory ref, revision, and timestamps.
4. Resolve every linked OpsMate instance and enumerate every custom session;
   supplied URLs are seeds, not an allowlist.
5. Retrieve stable trajectory IDs, harnesses, cutoffs, and database-tool calls.
6. Inspect the SEV snapshot, linked context, alerts, runbooks, and stakeholder
   tool activity. Dataset names are hints, never hardcoded truths.
   Union typed telemetry references from the SEV evidence pack, linked context,
   relevant metrics, and all trajectories. Resolve each table's current
   metadata and oncall ownership; record ownership mismatches and transfers.
7. Re-run selected bounded queries at the historical cutoff when authorized.
   On denial, use an approved immutable trajectory receipt or block the build.
   Never transcribe approximate values from prose.
8. Hash raw receipts before normalization and keep them private.
9. Stage sufficient needed and realistic unwanted evidence. Record duplicate,
   irrelevant, inaccessible, unsupported, and post-cutoff sources.
10. Measure source cardinality, bytes, time density, key frequency, skew,
    missingness, duplicates, and retry rates before transformation. Preserve
    these distributions in the scale plan. A small convenience sample cannot
    establish production-scale fidelity.

Fixtures prove portability only. They cannot satisfy production discovery,
fidelity, completeness, or independent-solvability gates.

The authoritative join is:

`SEV incident -> experiment run -> arm -> trajectory_ref -> harness reader`.

The trajectory-ref scheme identifies storage, not the harness. Resolve the
harness from the arm's AgentRef. For the live evaluator pipeline, preserve and
join the exact `(source_job_type_id, source_faas_instance_id)` pair because a
session ID can be reused or ambiguous.

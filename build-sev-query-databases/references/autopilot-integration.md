# OAOA autopilot integration

This skill builds one query-replay component. It does not build or publish a
complete benchmark task.

## Parent invocation

For an existing scaffold or component build, the parent uses:

```text
$oaoa-sev-task-autopilot
mode=develop-draft
source_kind=sev
draft=<absolute task or component path>
```

The stable SEV key and all production provenance stay author-only. The parent
must preserve the selected incident and may not fill a missing source with a
different incident.

## Required handoff

`scaffolding_summary.json` is the machine-readable handoff. Its
`parent_handoff` object declares:

- what component this skill completed;
- that the full task is not built;
- the required parent skill and mode;
- agent-visible component paths;
- private authoring paths that must never enter the task image;
- remaining lifecycle stages;
- blocking and non-blocking gaps.

The parent rejects a component whose validation failed, whose export is not
eligible, or whose mandatory gap is unresolved.

## Ownership boundary

This skill owns bounded query discovery, synthetic reconstruction, replay
materialization, native-looking clients, receipts, and component validation.

The autopilot owns task identity and deduplication, difficulty design,
instruction authorship, non-database evidence, recovery behavior, oracle,
grader, controls, calibration, reviews, provenance, contamination, novelty,
commit, push, and exact-SHA reconciliation.

The agent receives only the safe `task/` subtree. It never receives
`private/`, `replay/`, raw discovery, source mappings, classifications,
production IDs, or the build-root summary.

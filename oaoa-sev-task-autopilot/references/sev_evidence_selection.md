# Reusable SEV evidence selection

Applies to `source_kind: sev`. Local and scheduled runs use the same private
selection directory, supplied as `OAOA_SELECTION_DIR`; the local default is
`~/.local/share/oaoa/selection/sev`. This is a cache, not a parallel claim registry.
Across hosts, use an approved shared private store or reconcile against the
canonical registry. A host-local file cannot prove another author's source is free.

## Additional eligibility filter

Install the complete `tooling/sev-evidence-pack-v2/` directory from
`codimango/swe-bench-aai-labs-oaoa` and read its `SKILL.md`. Record the upstream
commit and tool hash. The installed skill directory is `EVIDENCE_SKILL_ROOT`;
the autopilot directory is `AUTOPILOT_SKILL_ROOT`. Use the unified command rather
than recreating discovery, acquisition, or evidence validation.

A SEV must pass the existing source and semantic dedupe gates **and** this filter:
closed, non-empty root cause, stored generated OpsMate gold with a Root Cause
section, and verified public visibility with privacy/security/safeguard flags
false. Unknown risk or denied/missing gold is unresolved, not a pass. Keep the
privacy/security exclusion enabled unless the user explicitly widens selection.
Oncall include/exclude flags narrow the authorized pool; they never replace these gates.

Check the installed upstream revision's contract before upgrading. Some 2.4
integration revisions perform private acquisition with
`risk_screening.status=not_performed` and allow low-confidence gold. Retain those
sources as `pending_eligibility_sevs`; neither behavior satisfies this autopilot's
eligibility gate. Missing risk information cannot establish a safe source.

## Find and retain a bounded set

Before discovery, load saved outcomes and refresh used/reserved source keys from
the canonical registry. Export those keys and explicit oncall exclusions as
`exclusions.json` with `skip_sevs` and `exclude_oncalls` arrays. Never turn an
unavailable registry into an empty clearance receipt. Retain its coverage gap.
`analyzed.json` has an `analyzed_sevs` array; initialize it empty only on the
first run, after reconciling existing author-only attempts.

Export the user-authorized candidate sheet as `authorized_candidates.json` with
a `sevs` array. When Landline discovery is explicitly authorized instead, use
the tool's bounded `--days` discovery without `--candidate-file`.

```bash
umask 077
python3 -I "$AUTOPILOT_SKILL_ROOT/scripts/selection_state.py" \
  --state-dir "$OAOA_SELECTION_DIR" check-access
```

Exit 3 means a recorded source-access block: stop discovery before invoking the
component. Keep `selection_status.json` and the full denial privately. Clear that
block only after a supported access/classification route actually changes and a
bounded read proves it. A new session, model, date or `AUTONOMOUS/READ` command
annotation does not establish changed asset access. A policy error is not a
reason to fan out over the saved corpus or omit risk checks.

After this check succeeds, run:

```bash
python3 -I "$EVIDENCE_SKILL_ROOT/scripts/sev_evidence_pack.py" \
  --candidate-file "$OAOA_SELECTION_DIR/authorized_candidates.json" \
  --skip-file "$OAOA_SELECTION_DIR/exclusions.json" \
  --analyzed-file "$OAOA_SELECTION_DIR/analyzed.json" \
  --selection-count 90 --discover-only \
  --out "$OAOA_SELECTION_DIR/discovery"
python3 -I "$AUTOPILOT_SKILL_ROOT/scripts/selection_state.py" \
  --state-dir "$OAOA_SELECTION_DIR" save-discovery \
  --receipt "$OAOA_SELECTION_DIR/discovery/.selection/effective.json"
```

The helper retains the discovery receipt, its hash, a tool-readable
`candidates.json`, and cumulative outcomes. `eligible_sevs` contains verified
selections; `retryable_sevs` retains per-source verification failures;
`pending_eligibility_sevs` retains incomplete classification or causal evidence.
Their union is the revalidation pool, never automatic eligibility. Discovery exit 2 with no
selected rows and no verification failures means an empty set; save it and stop
selection. With verification failures, retry the same retained sources before
declaring the pool exhausted. A command failure must not replace a previous valid
set. Retain truncation, denied reads, verification
failures, the discovery window, tool revision/hash, input/registry hashes and
requested filters in the author-only run receipt. Ninety is the retention cap,
not a claim of exhaustive eligibility. Discovery alone does not prove task
suitability, evidence-world sufficiency, a model gap, or task readiness.

## Resume and update

On subsequent local/scheduled runs, load `candidates.json`, `analyzed.json`,
`exclusions.json`, and `outcomes.json` first. Use `--candidate-file candidates.json`
to revalidate the saved pool with current metadata and fresh registry exclusions.
Do not rediscover the entire sheet merely because a new session started. Refresh
discovery when the pool is exhausted, the authorized pool/window or filter/tool
revision changes, or a saved eligibility fact is stale. An empty saved pool stays
empty; do not omit its flag and silently widen to Landline.

Before starting an attempt, persist its outcome; repeat when its disposition changes:

```bash
python3 -I "$AUTOPILOT_SKILL_ROOT/scripts/selection_state.py" \
  --state-dir "$OAOA_SELECTION_DIR" record S123456 \
  --status IN_PROGRESS --reason "Attempt started" \
  --evidence "$AUTHOR_ONLY_DIR/run_state.json"
```

`IN_PROGRESS`, `USED`, `UNSUITABLE`, and `REJECTED` enter `analyzed.json` and are
excluded from **new** selection. `RETRYABLE` retains the error and prior history
without permanently excluding an infrastructure/access failure. Imported
`analyzed_sevs` remain excluded until an explicit disposition changes them. Reevaluate a
rejected source only after recording the changed evidence or explicit owner
instruction. The helper locks writes and replaces JSON atomically; it does not
claim a source. Acquire the canonical fenced claim separately before authoring.

An existing owned attempt resumes by task/source identity and its run ledger;
it must not be silently replaced because its own source is in `analyzed.json`.
Named repair/develop runs keep their source and report any evidence-filter gap.

After selection and the claim/suitability gates, build the full evidence world
with the unified command. Reuse an existing bundle only after `--verify-existing`
and `validate_world.py` pass for matching source, cutoff and input hashes. Pass
matching `--sev-json`/`--evidence-pack` inputs to avoid recollection; keep all
raw/author-only content outside the task. Blocking world checks remain repair
items. Discovery-only mode builds no world and launches no Muse scouts.

For `logview-health-incident`, record `NOT_APPLICABLE_SOURCE_KIND` and retain its
existing source-aware filtering. Never invent a SEV to call this dependency.

## Push destination check

Before any authorized push, record the destination and dry-run the fully
qualified refspec `<expected-full-SHA>:refs/heads/<authorized-branch>`. Confirm
the output names only that destination before using the same refspec for the
real push. A source-only branch argument can map to its upstream branch under
`push.default=upstream`, including `main` after branching from `origin/main`.

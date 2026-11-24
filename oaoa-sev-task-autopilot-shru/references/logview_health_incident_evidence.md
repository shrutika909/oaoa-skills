# Logview Health Incident evidence and score acquisition

Apply this reference only to `source_kind: logview-health-incident`. Treat every command
as read-only discovery. Check the Meta CLI command annotation before first use and stop
for user confirmation if its control is not `AUTONOMOUS`.

An existing source plan is optional. When none exists, create an author-only source
ledger outside the submitted task package. Record direct versus derived claims, stable
source keys, causal timeline, source completeness, hashes, sanitization mapping, model
and grader receipts, unresolved gaps, and deliberately ungraded facts. Never fill a gap
by inference or fabricate a SEV identity.

## Resolve the source and original Opsmate run

For a live Health Incident ID:

```bash
meta logview.mid from-health-incident \
  --health-incident-id='<HEALTH_INCIDENT_ID>' --output=json --no-truncate
```

This is present-time only and must not be used in replay. With the Opsmate number:

```bash
meta opsmate.instance inspect --instance='<OM_NUMBER>' --output=json --no-truncate
meta opsmate.instance context --instance='<OM_NUMBER>' --output=json --no-truncate
meta opsmate.insights search --instance='<OM_NUMBER>' --limit=100 \
  --output=json --no-truncate
```

Record immutable source, instance, execution, session, agent, status, timestamp, linked
task/diff, and insight identities. Correlate by IDs and timestamps, never display names.

## Retrieve and prove the complete original trajectory

```bash
meta quality-toolkit.trajectory get --id='<SESSION_ID>' \
  --event-limit='<SAFE_CAP>' --output=json --no-truncate
```

Use a cap above the declared count. Save raw JSON author-only. Require declared and
materialized event/turn counts to match; record first/last timestamps, exact session,
truncation/pagination state, and SHA-256. Limited, sampled, missing, or mismatched output
is incomplete. Do not replace a successful auto-detected read with a framework-specific
reader.

## Retrieve Muse and Codex ACE experiment arms

Never infer Muse or Codex from arm order or friendly labels:

```bash
meta ace.experiment describe --id='<EXPERIMENT_ID>' --output=json --no-truncate
meta ace.experiment metrics --id='<EXPERIMENT_ID>' --unit=task \
  --output=json --no-truncate
meta ace.arm list --experiment-id='<EXPERIMENT_FBID>' \
  --columns=id,arm_name,eval_id,status,commit,orchestrator_type \
  --output=json --no-truncate
meta ace.prompt list --arm-id='<ARM_FBID>' --group-by-task \
  --output=json --no-truncate
```

For every prompt in each relevant arm:

```bash
meta ace.prompt transcript --id='<PROMPT_FBID>' --columns=all \
  --output=json --no-truncate
meta ace.grader list --prompt-id='<PROMPT_FBID>' \
  --columns=id,grader,did_pass,grade,action_status,session_id,trajectory_pointer \
  --output=json --no-truncate
meta ace.grader describe --id='<GRADER_RESULT_FBID>' --full-output \
  --output=json --no-truncate
```

Require terminal experiment, arm, prompt, and grader states; expected and materialized
prompt counts match; exact provider/model, harness/orchestrator, commit, prompt/tool
configuration, session/trajectory, cutoff, runtime, output, and grader contract exist.
Prompt completion is not success: use authoritative `did_pass` and `grade`. Preserve all
retry/error rows rather than selecting a favorable attempt.

## Retrieve native Opsmate experiment scores

```bash
meta opsmate.eval list --eval-name='<EVAL_NAME>' --created-within-days='<DAYS>' \
  --output=json --no-truncate
meta opsmate.eval status --run-id='<MOB_RUN_ID>' --output=json --no-truncate
meta opsmate.eval view-results --run-id='<MOB_RUN_ID>' --output=json --no-truncate
meta opsmate.eval compare --control-run-id='<CONTROL_MOB_RUN_ID>' \
  --treatment-run-id='<TREATMENT_MOB_RUN_ID>' --output=json --no-truncate
```

When authorized, query legacy `opsmate_eval` Scuba rows by exact session and bounded
window to corroborate investigator score/category/outcome, leak score/outcome, run/eval
names, agent, and trajectory source. ACL denial means `UNAVAILABLE`, not no row.

## Interpretation and retention

- Separate provider/model, harness, tool/context contract, grader, and score. Different
  harness/tool contracts make a `SYSTEM_ARM` comparison, not model-only.
- `eval_name` identifies an arm contract, not an immutable model revision.
- Keep Opsmate investigator and parallel leak grades separate.
- Do not compare ACE, Opsmate, OAOA, or Codimango numbers as one scale unless one frozen
  grader contract regraded every arm.
- Opsmate output is an arm result, never Health Incident gold. Grade arms independently
  against source-backed causal gold.
- Mark missing, expired, partial, report-only, unmapped, leaked, or unreadable evidence
  `UNSCORABLE` with its exact reason. Never infer zero or a model failure.
- Keep source IDs, URLs, outputs, trajectories, hashes, and score ledgers author-only.

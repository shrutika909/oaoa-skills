---
name: oaoa-sev-data-task-builder
description: Use when creating one OAOA Terminal-Bench or SWE-Bench task from a named mitigated SEV, a named Logview Health Incident task, or an authorized OAOA OpsMate experiment with valid paired outcomes.
argument-hint: <benchmark=tbench|swebench> <S_ID|T_ID|OPSMATE_EXPERIMENT_URL>
disable-model-invocation: true
user-invocable: true
---

# OAOA Incident Data Task Builder

Build one task from one explicitly supplied mitigated SEV, one explicitly supplied
Logview Health Incident task, or one incident selected deterministically from an
explicitly supplied OAOA OpsMate experiment. The invocation must explicitly select
`benchmark=tbench` or `benchmark=swebench`; never infer or auto-route the benchmark.

For Terminal-Bench, `oaoa-sev-task-autopilot` owns the full lifecycle. For SWE-Bench,
the applicable SWE-Bench flow owns the lifecycle. This skill owns only source
qualification, benchmark eligibility, and routing into that lifecycle. An incident's
operational evidence does not by itself make it a valid SWE-Bench task.

## Required skills

Read these completely before acting when their branch applies:

1. **TERMINAL-BENCH REQUIRED PARENT SKILL:** `oaoa-sev-task-autopilot`, shipped
   alongside this skill at `../oaoa-sev-task-autopilot/SKILL.md`.
2. **TERMINAL-BENCH CONDITIONAL COMPONENT:** `build-sev-query-databases`,
   shipped in this repo at `./build-sev-query-databases/SKILL.md`, including every
   reference it requires for the current phase. Use it only when the frozen public
   contract genuinely requires query-database evidence.
3. **TERMINAL-BENCH CONDITIONAL COMPONENT:** `ods-snapshot` from
   `tooling/ods-tool/authoring/SKILL.md` in the `codimango/swe-bench-aai-labs-oaoa`
   repo, including
   its referenced authoring, anonymization, data-model, and packaging docs. Use it only
   when the frozen public contract genuinely requires ODS counter or alert evidence.
4. **SWE-BENCH REQUIRED PARENT SKILL:** `team-aai:swebench-flow`
   (`fbcode/claude-templates/components/plugins/team-aai/skills/swebench-flow/SKILL.md`
   in fbsource, or the installed `team-aai` plugin) and its mandatory
   review, provenance, contamination, calibration, and validation skills. Select the
   correct public, licensed, or Meta-internal repository workflow from that skill; do
   not mix their source-materialization rules.

Use the complete `tooling/ods-tool` checkout containing the scripts. A copied
`SKILL.md` alone is insufficient.

## Invocation contract

Require exactly two explicit fields:

1. `benchmark=tbench` or `benchmark=swebench`; and
2. exactly one source:
   - one normalized `S[0-9]+` mitigated SEV;
   - one normalized `T[0-9]+` task that authoritatively resolves to a Logview Health
     Incident; or
   - one OpsMate experiment URL of the exact form
   `https://opsmate-experiment-console.internalmeta.com/experiments/<ID>/metrics`
   (an explicitly labeled experiment ID is also accepted).

Record exactly one `source_kind`: `sev` for an `S` source or
`logview-health-incident` for a `T` source. A `T` number is a task identifier, not the
stable source key: resolve and retain author-only the linked Health Incident plus exact
Logview context and MID. Require the Health Incident to be resolved or closed and to
have enough retained evidence to prove its causal mechanism. Never invent a Source SEV,
Health Incident ID, Logview MID, repository, patch, or test.

A named source uses the lifecycle's develop/new-source path. An experiment authorizes
selection from that experiment only. Never combine an experiment with a separately
named incident, silently widen to another experiment, substitute after selection, or
splice incidents. Missing `benchmark`, ambiguous source kind, or a `T` task that does
not resolve authoritatively is a stop condition.

### Experiment selection

Use the supported read-only export, not browser scraping:

```bash
meta opsmate.experiment export-runs \
  --experiment-id=<ID> \
  --limit=10000 \
  --columns=all \
  --output=json
```

Keep the raw export author-only. Before reading trajectory bodies:

1. Verify the returned `experiment_id` equals the supplied ID and retain its
   `schema_version`, `exported_at`, and run-count receipt.
2. Group by normalized `incident.short_name`; accept only `S[0-9]+` or `T[0-9]+` and
   resolve a `T` to its stable Logview Health Incident key before deduplication. Require one comparable
   baseline/Optimate run plus one Muse treatment run for the same
   `incident_artifact_id`. Use `arm_role` and recorded experiment metadata; never infer
   an arm only from a convenient name.
3. Reject missing trajectories, unsupported or incomplete harness records, mismatched
   targeting revisions, duplicate/conflicting pairs, leaked or post-cutoff evidence,
   and rows whose comparison validity does not support the intended contrast.
4. Join the authorized OAOA candidate registry by the source's canonical stable key.
   Prefer a genuine
   Optimate-success/Muse-failure contrast, then rank lexicographically in this exact
   order by: unused/unclaimed status,
   comparison validity, evidence confidence, causal gold, observable recovery,
   cutoff safety, dedupe status, and descending registry priority. Break a remaining
   tie by source-kind order (`sev`, then `logview-health-incident`) and ascending numeric
   source ID.
5. Run the parent's canonical registry and fenced-claim gates. Write an author-only
   `selection.json` containing the experiment receipt, paired run IDs and hashes,
   registry row hash, ranking inputs, exclusions, selected source kind, stable source
   key, and selected task/SEV. Do not copy raw
   reports or trajectories into it.
6. Freeze that source before private trajectory research. If no candidate passes every
   gate, stop with `NO_ELIGIBLE_EXPERIMENT_CANDIDATE`; never fall back to an unpaired
   or lower-integrity incident.

Experiment selection requires a valid pair even when a row looks intrinsically
interesting. A provisional, single-arm, missing-trajectory, or metadata-only row may be
reported for later direct investigation, but it MUST NOT be selected by this experiment
path or treated as evidence of a model score gap. The user may separately invoke the
skill with that named `T` source; it must then pass the direct-source evidence and
benchmark eligibility gates independently.

## Benchmark eligibility

### Terminal-Bench

Require a deterministic offline operational environment with meaningful multi-step
investigation, agent-visible falsifying evidence, a safe recovery action, and an
observable recovered state. Query-database and ODS components are evidence capabilities,
not universal requirements. Use either, both, or neither according to the frozen public
contract. If required production evidence cannot be anonymized and replayed faithfully,
stop; do not fabricate counters, logs, query results, or recovery behavior.

### SWE-Bench

Require all of the following before scaffolding:

1. an authorized repository and track-specific materialization path;
2. an exact cutoff-safe base revision containing the defect;
3. a concrete code change that fixes the incident's mechanism rather than merely its
   symptom;
4. a reproducible fail-before signal on the base revision; and
5. solution-independent tests that pass after the reference patch and reject a no-op.

The incident supplies provenance and requirements; it does not authorize copying raw
internal evidence into the task. Query-database and ODS builders do not run on this
branch. If the defect is primarily operational, lacks a reproducible repository state,
or cannot support fail-before/pass-after tests, stop with
`NOT_ELIGIBLE_FOR_SWEBENCH`; do not convert an investigation narrative into a fictional
code task.

For persistent end-to-end execution, the user must invoke it through `/goal` and
explicitly authorize the selected benchmark lifecycle's normal task-scoped calibration,
commit, push, and exact-SHA validation. This never authorizes submission, release,
landing, autoland, publication, or outreach.

## Workflow

1. Record `benchmark`, `source_kind`, canonical stable source key, and exact authorized
   source in one author-only state file. For an experiment, perform the bounded selection
   above first. Run the canonical registry, semantic-dedupe, eligibility, and fenced-claim
   gates before private evidence loads.
2. Research the frozen source and write an author-only evidence ledger. Preserve exact
   experiment/run/trajectory/score completeness and provenance. Missing evidence is
   `UNSCORABLE`, never score zero or model failure.
3. Apply the selected benchmark's eligibility gate. Do not switch benchmark because the
   chosen branch fails; report the failed gate and require a new explicit invocation.
4. For `benchmark=tbench`, start `oaoa-sev-task-autopilot` with the recorded source kind.
   Freeze one public task contract, then run query-database and/or ODS components only
   for conclusions that require them. Keep raw evidence and private receipts outside the
   submitted task. Return control to the parent for authorship, Oracle, adversarial and
   negative controls, static review, five-trial calibration, provenance, contamination,
   novelty, commit, push, ingestion, and exact-SHA validation.
5. For `benchmark=swebench`, start the applicable `team-aai:swebench-flow` branch. Freeze
   the repository and base revision, reproduce fail-before, build the reference patch,
   add solution-independent tests, prove pass-after and no-op rejection, then complete
   its mandatory review, provenance, contamination, calibration, packaging, and
   exact-SHA validation gates. Follow current model-authorship restrictions for
   `instruction.md`, tests, and agent-visible files.
6. In either branch, ship no source incident ID, real name, internal URL, raw production
   row, trajectory, hidden label, private mapping, or answer-bearing receipt.

## Completion

Completion is `READY_FOR_HUMAN_SUBMISSION` for the exact ingested full SHA under the
selected benchmark's authoritative lifecycle. The receipt must identify the source kind,
stable source key, benchmark, evidence completeness, applicable component receipts, and
proof that private artifacts were excluded. A component build, local task directory,
commit, feature-branch push, or partial validation is not completion. This skill never
authorizes submission, release, landing, publication, or outreach.

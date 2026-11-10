---
name: oaoa-health-incident-harvester-farm
description: Use when farming a Terminal-Bench task from a Logview Health Incident task row or an authorized OAOA OpsMate experiment containing Health Incident trajectories.
---

# OAOA Health Incident Harvester Farm

Turn one eligible Logview Health Incident into a source-safe external idea, then use the
shared `$oaoa-harvester-farm` Harvester lifecycle. Never reinterpret a `T…` task as a SEV.

## Current capability

`NOT_PRODUCTION_READY`: this skill has contracts and fixture-tested local adapters, not a
live end-to-end task factory. Do not describe it as ready to farm, create, validate, or
submit a real task until every blocker below is resolved on deployed revisions.

| Capability | Current state | Required proof |
|---|---|---|
| Health Incident registry claim | Deployed | Client is on `oaoa-tbench/main`; trusted projection landed in `D130332724`. A real source still needs a live read plus fenced claim for remote intake. |
| Live acquisition | Missing | Authoritative live command receipts for source, trajectories, scores, and dedupe |
| Integrity chain | Missing | One hash chain from acquisition through the exact final brief |
| Shared Harvester worker | Missing | External intake through worker terminal state on the same chain |
| Terminal-Bench | Contract only | All local and cloud gates below |
| SWE-Bench | Unsupported | A separate implemented and tested source-to-SWE contract; never improvise one |

`BLOCKED_EXTERNAL_INTAKE_INTEGRITY_CHAIN`: private source research may start, but external-idea
intake must stop until the selected source's acquisition, trajectory, score, dedupe,
guard, world, scout, design, and brief hashes are chained in one fail-closed receipt.
The current local adapters validate their own inputs; they do not prove that author-supplied
PASS fields came from the authoritative live commands.

`REGISTRY_DEGRADED_LOCAL_ONLY`: Health Incident origin support is deployed, but a transient
registry outage must not prevent author-private research or a local prototype when every
accessible repository, card, retired-task, rejected-task, and semantic-dedupe check is
clear. The outage still blocks shared-board intake, publication, Codimango import, and
submission. A known conflict blocks all work. Do not encode a Health Incident as a SEV,
mint a parallel registry, or treat the Drive rollout plan as registry data.

The existing SEV world builder and `sev-harvester-flow` remain invalid substitutes.

## Required skills and references

Read completely before acting:

1. **REQUIRED PARENT:** `$oaoa-harvester-farm` for Harvester preflight, remote safety,
   external intake, authoring, judges, and readiness.
2. **REQUIRED SOURCE CONTRACT:** `$oaoa-sev-data-task-builder`; use only its
   `logview-health-incident` and authorized-experiment branches.
3. **REQUIRED QUALITY CONTRACT:** `$oaoa-sev-task-autopilot`, especially
   `references/logview_health_incident_evidence.md`.
4. **REQUIRED EXPORT CONTRACT:**
   `tooling/build-sev-query-databases/references/anonymization-contract.md` and, when
   LogView evidence is materialized, `references/logview-contract.md`.
5. **REQUIRED LOG ANONYMIZATION GUIDE:**
   [Anonymizing logs for a Cyber Bench task](https://docs.google.com/document/d/1MrQRKafyDLVpDIHU7c4q1WfIM7EB6hvSne3wzFy-d_k/edit?tab=t.0#heading=h.q3pmxopxs8nn).
   Its `log_anon` procedure is mandatory whenever log-shaped source data is staged or a
   log-derived fixture is produced. It augments, and never replaces, fictional reconstruction.

## Invocation

Accept exactly one source:

```text
$oaoa-health-incident-harvester-farm create from T123456
$oaoa-health-incident-harvester-farm create from experiment 123456789
$oaoa-health-incident-harvester-farm resume <author-only-run-directory>
```

Initial scope is Terminal-Bench only. Reject `S…`, multiple sources, an unbounded Sheet
scan, or a mixed T-plus-experiment request.

Record `selection_mode: named-t` or `selection_mode: authorized-experiment` before any
private source read. A T mentioned as a candidate without an experiment ID uses
`named-t`; never infer or widen to an experiment.

## Workflow

### 1. Preflight and remote-safety gate

Run the parent's `scripts/preflight.py`. Record the Harvester revision, task repository,
product baseline, board identity, and `external_idea_intake` result. Inspect the live
worker and `[review] auto_submit` before source research.

Do not create a card unless the user's authority covers every later action a shared
worker can take, or an observed task-scoped hold prevents those actions.

Preflight has two separate effects:

- Missing board binding, board synchronization, or safe worker policy blocks only Harvester
  card intake and shared-worker execution. It does **not** block authorized author-private
  experiment export, source resolution, evidence acquisition, fictional reconstruction, or
  creation of a validated local brief.
- Missing source access, inaccessible dedupe coverage, a known duplicate, or an unsafe data
  classification blocks source work at the corresponding fail-closed gate.

When the board is unavailable but the private-source gates pass, continue through Step 7 and
stop at `LOCAL_BRIEF_ONLY`. Never describe the private queue request itself as the idea or card.

### 2. Resolve and freeze one source

For an experiment, use the supported export rather than browser scraping:

```bash
meta opsmate.experiment export-runs \
  --experiment-id=<ID> --limit=10000 --columns=all --output=json
```

Require a comparable baseline/Optimate arm and Muse treatment arm for the same
`incident_artifact_id`. Use recorded arm roles; never infer identity from ordering or a
friendly label. Reject incomplete, conflicting, leaked, post-cutoff, or revision-mismatched
pairs.

A `T…` value is only a task locator. Resolve it authoritatively to one closed/resolved
Health Incident and then to the stable private key `(LogView context, MID)`. Run registry,
claim, repository, card, retired-task, rejected-task, and semantic dedupe against that key
before retrieving trajectory bodies.

The registry rollout document at Drive file
`1CtS5iVsMrWh_vb6dJb31fHWOn9rEMAft` describes the lifecycle; it is not the registry and
must never be updated as if it contained claims. The authoritative store is Knots namespace
`oaoa/task-registry`. Use only a client whose declared origin contract explicitly accepts
the Health Incident stable key.

Write the registry attempt plus accessible dedupe results to a private JSON input and run:

```bash
python3 scripts/registry_gate.py /absolute/path/registry_gate_input.json \
  --output /absolute/path/registry_gate_receipt.json
```

The gate has exactly three useful outcomes:

- `FENCED_CLAIM_CONFIRMED`: private research, local prototyping, and later external
  intake may proceed, subject to every remaining gate.
- `REGISTRY_UNAVAILABLE_CONTINUING_LOCAL`: private research, fictional reconstruction,
  brief creation, and local prototyping may proceed. Stop before external intake and
  retain the outage-attempt receipt.
- `KNOWN_DUPLICATE_BLOCKED` or `REGISTRY_CONFLICT_BLOCKED`: stop and do not research,
  scaffold, intake, or publish that source.

For an authorized experiment, rank deterministically as usual. During an outage, select
at most one otherwise eligible, accessible-dedupe-clear candidate for local-only work.
Never treat the absence of registry data as proof that the source is unused.

Freeze the source after selection. Never substitute or splice another incident.

Store private state under an opaque path such as:

```text
/data/repos/oaoa-author-only/health-incident-<key-sha256-prefix>-harvester-farm/
```

This path overrides the parent's `<SEV>-harvester-farm` default. A registry outage permits
only the mechanically gated local-only scope above. Missing accessible dedupe coverage,
an unresolved conflict, or a known duplicate remains a fail-closed stop before trajectory
reads. A fenced claim remains mandatory before external intake.

### 3. Acquire complete private evidence

Follow the autopilot Health Incident reference exactly:

- resolve Health Incident → LogView context/MID;
- inspect the original OpsMate instance, context, and insights;
- retrieve the complete original trajectory;
- retrieve every relevant ACE Muse/Codex prompt, transcript, grader, retry, and error;
- retrieve native OpsMate evaluation results when applicable;
- preserve model, harness, tool contract, cutoff, leak, runtime, score, and grader provenance.

Declared and materialized trajectory counts must match. Limited, sampled, truncated,
expired, missing, report-only, leaked, or unmapped evidence is `UNSCORABLE`, never score
zero and never a model failure. OpsMate output is an arm result, not causal gold.

Keep raw exports, trajectories, scores, URLs, IDs, hashes, and source mappings author-only.

Use the `oaoa-sev-task-autopilot` Health Incident evidence method to derive the task idea from
the complete comparison, not from the incident title or final score alone. Privately identify:

- which pre-cutoff evidence the Muse arm observed, missed, or misinterpreted;
- the exact reasoning branch, tool failure, retry, or incomplete retrieval associated with the
  outcome;
- which competing explanation remained plausible and which reachable evidence falsifies it;
- which recovery action and observable final state are supported by reviewed causal gold.

Muse behavior is design evidence, not the answer key. A failed or lower-scoring Muse arm is not
proof of the root cause; an incomplete, leaked, expired, or unmapped arm remains `UNSCORABLE`.
Record the private failure analysis and its trajectory/score hashes before designing the
fictional task.

Fixture success is never live acquisition proof. Each adapter invocation must record the
exact supported command, deployed tool revision, request parameters or their private hash,
source revision/cutoff, response hash, completeness fields, timestamp, and exit status.
If any required source was supplied manually or its live receipt is missing, stop with
`LIVE_ACQUISITION_UNPROVEN`.

### 4. Create an export-safe fictional specification

Do not send raw trajectories or production extracts to an LLM. Privately abstract only:

- schemas and relationships;
- causal and temporal shapes;
- failure and recovery sequences;
- contradictions, decoys, and reachable falsifiers;
- safe recovery constraints and observable final state.

Production-derived task data must be regenerated from a fictional specification. Simple
renaming or deterministic pseudonymization is not an export control. Require independent
PASS results for identity safety, confidentiality safety, and technical fidelity.

Apply the required `log_anon` guide as a second, mechanical defense whenever log-shaped data is
materialized:

1. Independently confirm the input is non-DSS4. The CLI heuristic is not sufficient, and
   `--acknowledge-dss4-risk` requires a recorded independent classification decision.
2. Never anonymize in place. Use a fresh output directory for every run so salts and leftovers
   cannot mix.
3. Run a cheap dry run first, then the final pass with secret scanning enabled. `--no-priner` is
   allowed only while the documented use case is unavailable; `--no-secret-scan` is not valid
   for a release candidate.
4. Preserve the command, tool revision, input-tree hash, output-tree hash, report hash, stage
   availability, exit status, and per-label counts in the private acquisition chain. Never
   persist the salt, alias map, raw values, or aliases in the report.
5. Require zero matches for selected known cleartext canaries, equal expected/materialized file
   counts, no skipped non-UTF8 or failed files, and review of the value-free JSONL report.
6. Treat bare usernames, Windows SIDs, `DOMAIN\\user`, user-profile paths, filenames, directory
   names, and non-Latin names as known coverage gaps requiring an additional guard or rejection.
7. Never permit credential verification against real providers. A scanner configuration that
   performs network verification is a hard stop.

`log_anon` output derived from production logs remains author-private unless the fictionalization
and export contracts independently permit it. Format-preserving pseudonyms are not permission to
ship production-derived records.

When LogView is part of the public task, preserve only approved operation semantics and
MID→sample→thread relationships through fictional resources. Never export real context,
MID, queries, messages, stacks, paths, distributions, or implementation details.

### 5. Build and validate the typed incident world

Create a private abstract specification matching
`references/incident-abstract-spec.schema.json`, then build hash-bound artifacts:

```bash
python3 scripts/build_incident_world.py \
  --abstract-spec /absolute/path/incident_abstract_spec.json \
  --guard /absolute/path/identifier_guard.json \
  --out /absolute/path/world
```

The acquisition workflow produces the first four ledgers and guard below. The world
builder consumes the fictional abstract spec plus guard and produces the last two:

- `source_receipt.json`: source kind, opaque stable-key hash, closed status, and source hashes;
- `trajectory_ledger.json`: every arm and completeness/cutoff/leak result;
- `score_ledger.json`: authoritative grader results without collapsing score scales;
- `dedupe_receipt.json`: registry gate plus repository/card/retired/rejected/semantic checks;
- `incident_world.json`: label-free fictional evidence only;
- `identifier_guard.json`: exact protected tokens, distinctive one-to-three-word private
  phrases, and four-word source n-grams.

The world schema must be `oaoa.agent-incident-world.v1`, bind its exact content hash, and
contain no source IDs, raw prose, internal URLs, answer labels, or post-cutoff evidence.

Require `build_receipt.json` status `PASS`. Do not hand-write or edit a receipt to bypass
the builder.

Until one chain receipt binds the authoritative acquisition ledgers to the exact guard,
world, two scout inputs/outputs, design, and brief, stop with
`BLOCKED_EXTERNAL_INTAKE_INTEGRITY_CHAIN` before external intake. Do not treat matching text fields
or manually copied hashes as proof of that chain.

The authoritative chain is exactly:

```text
acquisition -> trajectories -> scores -> dedupe/claim -> identifier guard ->
fictional specification -> incident world -> directional scout -> misleading scout ->
private design -> external brief
```

Every edge binds the predecessor's canonical SHA-256 and the successor's exact input and
output SHA-256. One terminal `oaoa.health-incident-intake-chain.v1` receipt names every
artifact hash, live command receipt, deployed revision, registry-gate outcome, and final
brief hash. A missing, duplicate, reordered, manually asserted, or mismatched edge is a
hard stop. `REGISTRY_UNAVAILABLE_CONTINUING_LOCAL` can produce only a local-only chain;
it can never satisfy external intake.

### 6. Run exactly two independent read-only scouts

After the typed-world adapter exists, run two fresh Muse sessions over only the label-free
fictional world:

1. `directional`: find underused relationships and causal discriminators.
2. `misleading`: find plausible wrong paths and the reachable evidence that kills each.

Both sessions must use explicit approved models, disable writes, shell, web tools,
user-input requests, approvals, and session logging. Both must succeed. Do not silently
replace a failed scout or expose source mappings.

Merge them deterministically into a private seed, preserving independent session/model
receipts and hashes.

Record both runs in `oaoa.incident-scout-runs.v1`, then validate them:

```bash
python3 scripts/validate_scout_runs.py \
  --build-receipt /absolute/path/world/build_receipt.json \
  --runs /absolute/path/scout_runs.json
```

This must prove exactly the `directional` and `misleading` roles, distinct session IDs,
explicit provider/model identity, input-hash binding, output-hash binding, and PASS status.

### 7. Produce the source-safe design and brief

Use `references/design-prompt.md` and
`references/health-incident-harvester-idea.schema.json`. The private design contains a
novelty check, one to three bounded levers, and `do_not_mention` classes.

Convert it to Harvester's smaller external-idea schema. Validate before intake:

```bash
python3 scripts/validate_external_brief.py /absolute/path/farming_brief.json \
  --guard /absolute/path/identifier_guard.json
```

This validator augments Harvester; it does not replace human source-safety review.

### 8. Join the shared Harvester lifecycle

Only after every prior receipt passes, the intake-integrity blocker is resolved, and the
registry gate says `FENCED_CLAIM_CONFIRMED`,
return to `$oaoa-harvester-farm` at its
external-idea-intake step. Reuse its exact intake, isolated authoring node, same-tree
Oracle reproof, fidelity/environment/realism/calibration judges, remote-safety rules, and
Codimango readiness vocabulary.

Never run the SEV `build_world.py`, SEV scout contract, or old `sev-harvester-flow`
controller for a Health Incident.

Require an end-to-end worker receipt binding the intake-chain hash, Harvester revision,
card identity, authoring node, produced task tree hash, every judge result, and terminal
worker state. Local adapter tests, a card, or a task directory do not prove worker E2E.

### 9. Prove the Terminal-Bench task

After the worker produces a task, inherit stricter parent/builder rules and require all
of these on the exact task-tree hash:

- verifier isolation mode proven in the same environment used by validation;
- network and egress policy validation, including fail-closed unavailable checks;
- Oracle plus Eval GT/TBR success;
- completed legitimate-model calibration with infrastructure failures excluded;
- current provenance and contamination results;
- reward parsing through an isolated, fail-closed parser that rejects missing, malformed,
  multiple, non-finite, out-of-range, or agent-controlled reward data;
- fidelity, environment, realism, security, and task-quality gates;
- shared-worker E2E receipt and authoritative intake-chain receipt.

Any missing, stale, skipped, fixture-only, differently hashed, or unavailable required
gate leaves the task `LOCAL_PROTOTYPE_ONLY`; it is not Codimango-ready.

## Stop conditions

Stop before intake for any of these:

- unresolved T→Health Incident→context/MID mapping;
- open/nonterminal incident or insufficient causal gold;
- known registry or accessible-dedupe conflict;
- missing accessible dedupe coverage;
- missing/incomplete/leaked/post-cutoff trajectory or invalid arm pairing;
- production evidence that cannot be fictionally reconstructed faithfully;
- missing identity, confidentiality, or fidelity gate;
- missing or invalid typed-world/scout adapter receipt;
- missing authoritative live receipt chain from source acquisition through brief;
- any protected token or source n-gram in the design, card, or task tree;
- remote worker policy exceeding current authorization.

Do not switch incidents to hide a stop condition.

## Completion

Use these non-overlapping states:

| State | Meaning |
|---|---|
| `LOCAL_BRIEF_ONLY` | One source-safe brief exists, but the registry gate is local-only or the authoritative intake chain is incomplete. No card or remote handoff. |
| `BRIEF_READY` | One source-safe brief and authoritative intake-chain receipt exist. No task-readiness claim. |
| `LOCAL_PROTOTYPE_ONLY` | A task tree exists but at least one worker, local, or cloud gate is missing. Never hand to Codimango. |
| `LOCAL_TASK_READY` | Local Oracle, verifier, isolation, egress, security, and reward gates pass on one tree hash. Cloud gates remain. |
| `CLOUD_GATES_PASS` | Eval GT/TBR, legitimate-model calibration, provenance, contamination, and quality gates pass on that same hash. |
| `SUBMIT_READY` | Registry lifecycle, worker E2E, task identity, repository revision, and all prior receipts reconcile. Human may submit. |
| `SUBMITTED` | Human-authorized Codimango submission exists. |

Never call `LOCAL_BRIEF_ONLY`, `BRIEF_READY`, a worker card, a local directory, or
`LOCAL_TASK_READY` a full task. SWE-Bench has no completion state in this skill because
it is unsupported.

The skill never authorizes publication, review submission, acceptance, release, merge,
or landing.

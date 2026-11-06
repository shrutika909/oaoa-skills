---
name: oaoa-sev-task-autopilot
description: Use when developing, creating, or repairing an AAI Labs OAOA Terminal-Bench RCA task sourced from a mitigated SEV or eligible Logview Health Incident until its exact SHA is ready for human submission, including idea expansion, difficulty design, source evidence, trajectories, scores, deduplication, approved-model instruction authorship, review, calibration, provenance, and validation.
---

# OAOA Incident Task Autopilot

Create one fair, novel OAOA task from one real mitigated SEV or eligible Logview Health Incident.
The deliverable is a human-release candidate with an exact-SHA receipt, not merely a task directory.

Every run has exactly one `source_kind`: `sev` or `logview-health-incident`. Record it before
source research. Never apply SEV-only facts, metadata, or eligibility rules to a Logview source.

## Modes

Choose exactly one mode from the invocation. If it is missing or ambiguous, ask before
changing anything.

### `new`

Select one unused source of the explicitly declared `source_kind`, design and build a
new task, and carry it through the complete lifecycle in this skill. If `source_kind` is
missing or ambiguous, ask before loading private source details or changing anything.

Start persistent new-task work with:

```text
/goal $oaoa-sev-task-autopilot
mode=new
source_kind=<sev or logview-health-incident>
Select from <authorized candidate source> and continue until the exact pushed SHA is
READY_FOR_HUMAN_SUBMISSION.

This goal authorizes required local calibration, task-scoped commits, pushing the frozen
candidate, and exact-SHA validation. It does not authorize submission or release.
```

### `develop-draft`

Develop an unregistered scaffold, partial package, author-only brief, or basic idea into
one candidate. Read `references/develop_draft.md` completely and use its goal template.
Missing registration, plans, reviews, commits, or runs are work to perform, not blockers.
Do not replace the core idea; extensions must be coherent, visible, and falsifiable.

### `repair-existing`

Repair one named existing task without changing its source incident, source kind, task
identity, or core problem. The invocation must identify the task by Codimango task ID,
repository path, or unambiguous task slug. Resolve and record the current exact SHA
before editing. Infer `source_kind` only when author-only records prove it.

1. Read the existing author-only `run_state.json`, task package, Codimango status,
   validation results, exact-SHA reviews, and trial evidence. Create `run_state.json`
   outside the submitted task directory when none exists.
2. Build one consolidated repair queue covering every failed, stale, missing, and
   pending gate. A current Avocado `too easy` finding or three or more genuine passes
   out of five is a failed calibration gate and must add difficulty redesign to this
   queue. Do not stop after fixing the first item or after one validation passes.
3. Diagnose each distinct failure class before editing. Reproduce ambiguous trial
   failures with `create-trial-sandbox`. Use `review-task-tbench-v2` for complete
   read-only review, not as a substitute for runtime validation.
4. Preserve the source incident, source kind, and task contract. Never switch incidents,
   splice another incident, or redesign the evaluated problem without explicit user
   confirmation.
5. After every material change, invalidate affected receipts and rerun all downstream
   gates: instruction authorship/hash when applicable, spec-to-test matrix, static
   review, Oracle, negative controls, trial classification, calibration, provenance,
   contamination, novelty, commit/push, and exact-SHA Codimango validation.
6. Update author-only `run_state.json` after each phase with task identity, source kind,
   stable source key, source references, Opsmate/experiment/trajectory receipts,
   repository, exact SHA, package hash, completed and invalidated phases, review IDs,
   trial IDs and classifications, reviewer-feedback ledger, current repair queue,
   blockers, and next action.
7. Continue until the exact pushed SHA is ready for human submission. `Accept` from one
   review, one repaired test, one green trial, or one successful validator is never a
   completion condition.

Human submission, acceptance, release, and landing remain outside this mode unless the user separately authorizes the specific action.

### Repair invocation for a Logview task

Use this shape when starting a persistent repair goal for an existing Health
Incident-derived task. `/goal` is required; prose that merely says "create a goal" does
not activate persistent goal handling.

```text
/goal $oaoa-sev-task-autopilot
mode=repair-existing
task=<absolute-task-path, Codimango ID, or slug>

Continue repairing every failed, stale, missing, or pending gate until the exact pushed
SHA is READY_FOR_HUMAN_SUBMISSION.

Source kind: logview-health-incident (NOT a SEV).
Author-only source plan: <absolute-plan-path, or NONE>.

If the source plan is NONE, reconstruct the source from authoritative Logview, Health
Incident, Opsmate, trajectory, experiment, reviewed-fix, and linked-task records. Create
an author-only source ledger outside the submitted task directory before editing. Do not
invent missing facts.

Preserve the task identity, Logview context + MID, Health Incident, core mechanism, and
source kind. Never invent a Source SEV or an unsupported origin tag. Retrieve and retain
author-only the original Opsmate record and all linked Muse/Codex experiment trajectories
and authoritative scores with model, harness, run, prompt, session, trajectory, grader,
cutoff, leak, and completeness provenance. Missing or partial evidence is UNSCORABLE,
not score zero and not a model failure.

Build one repair queue for all failed, stale, missing, and pending gates. Apply the
too-easy loop at 3/5 or higher and the report-contract repair gate. Do not splice another
incident. Run fresh calibration after every task-byte change that invalidates prior
results. Once all pre-push gates pass, commit and push the frozen candidate and reconcile
the exact-SHA validation. Keep instruction.md under the approved K3/Muse authorship
rules. Do not submit, accept, release, land, publish a diff, contact anyone, or enable
autoland.
```

## Required foundations

Before acting, read the repository versions of `sev-investigation-task` and
`sev-to-codimango-task` completely, including each reference required for the current
phase. Use the latter as the authoritative quality lifecycle, adapting its source steps
without pretending a Logview source is a SEV. Also read the OAOA project instructions
and `docs/reference/sev_to_synthetic_task_playbook.md`. For a Logview source, read the
supplied Logview task plan when one exists and current Logview/Opsmate investigation
instructions. A source plan is helpful but not required.

Source locations (already out there — clone, do not copy into this repo):
- `.agents/skills/sev-investigation-task/SKILL.md` and
  `.agents/skills/sev-to-codimango-task/SKILL.md` (with all `references/` and
  `scripts/`) in the `codimango/oaoa-tbench` repo (same origin as task checkouts).
- `docs/reference/sev_to_synthetic_task_playbook.md` in the `codimango/oaoa-tbench`
  repo (also present in task checkouts).
- `team-aai:swebench-flow` and `create-trial-sandbox` from the installed `team-aai`
  plugin (sources in fbsource at
  `fbcode/claude-templates/components/plugins/team-aai/skills/`).
- `review-task-tbench-v2` from the `team-aai` plugin install; canonical sources live
  under `team-aai-dev` / `team-aai/quality` in fbsource, so confirm which revision
  your install carries before pushing.

SEV-only eligibility and metadata rules remain authoritative for `source_kind: sev`
only. For `logview-health-incident`, inability to verify the accepted non-SEV origin
marker blocks commit, push, and submission, but does not block safe local research,
design, or repair.

This skill adds OAOA candidate selection, live review-learning, and first-party
instruction authorship. It does not weaken the repository skill's gates.

## Run contract

1. Create a persistent goal only when the user explicitly asks for persistent/end-to-end
   completion. Record the exact authorized mutations; blanket language never authorizes
   unrelated outreach, acceptance, release, or task substitution.
2. Fetch the latest `codimango/oaoa-tbench` state. Work in a dedicated clean worktree;
   never use a checkout containing another session's changes.
3. Read the supplied candidate sheet and the canonical cross-author registry. Consider
   only resolved sources not already used or reserved by another author — replace the
   two hardcoded author names below with the current author list from the registry
   before selecting. Dedupe by the canonical stable source key before loading incident
   details: SEV number for `sev`, or Logview context plus MID for
   `logview-health-incident`. Then run semantic dedupe across active, draft, retired,
   rejected, and cross-repository tasks. Default registry owners at time of writing:
   Shrutika Naik, Akash Jothi.
4. During pre-selection, reject unsuitable sheet rows and continue to the next row when
   candidate selection was authorized. Once one source is selected and research begins,
   never substitute another without explicit confirmation. Pick the candidate only after
   verifying causal gold, task suitability, safe synthesizeability, observable
   discriminators, and a coherent recovery action. A Logview candidate must have a
   resolved or closed Health Incident, a stable context plus MID, and enough retained
   evidence to prove its causal mechanism. If it fails, record the reason and evaluate
   another candidate only when candidate selection was explicitly authorized. Never
   splice incidents merely to raise difficulty.
5. Before design, perform a bounded read-only audit of the latest available full-SHA Codimango
   full-task/deep reviews for current OAOA drafts owned by the registry's active
   authors. Extract
   generalized lessons by category: fairness/observability, verifier correctness,
   leakage, novelty, provenance, calibration, metadata, and infrastructure. Never copy
   task text, hidden answers, reviewer-only gold, or task-specific fixes into the new task.
   Read only the report fields needed for that categorization. If a draft has no review
   for its current SHA, record `NO_CURRENT_SHA_REVIEW` rather than using an older verdict.
6. Research the selected source and every qualifying Opsmate or experiment trajectory.
   Keep source records, raw trajectories, scores, review reports, model receipts, and
   validation artifacts in an author-only directory outside the submitted task package.
   Never put a Logview MID, Health Incident ID, Opsmate ID, experiment/run/session ID,
   internal URL, production crash prose, employee identity, or raw trajectory in the
   submitted package or agent image.
7. Design difficulty from realistic temporal reconciliation, cross-surface evidence,
   causal ambiguity, mutation scope, and reachable falsifying evidence. Put believable
   decoys in the environment. Keep `instruction.md` neutral and outcome-based. Do not
   target Avocado, pad prose, hide required evidence, add arbitrary waiting, or ask a
   model to become confused.

## End-to-end execution authority

An invocation that uses `/goal` and requires an exact pushed SHA at
`READY_FOR_HUMAN_SUBMISSION` explicitly authorizes the normal task-scoped operations
needed to reach that state:

- edit the named task and author-only evidence;
- run required local tests, Oracle, negative controls, static reviews, provenance,
  contamination, novelty, and fresh calibration batches;
- classify and reproduce failed trials;
- create task-scoped commits after all pre-push gates pass;
- push the one frozen candidate and wait for its automatically started validation;
- perform a necessary scoped calibration/validation rerun for the expected exact SHA
  when the existing result is stale, invalidated, missing, or infrastructure-failed.

This authority does not include human submission, acceptance, release, landing,
autoland, unrelated outreach, incident substitution, or unrelated repository changes.
More restrictive instructions in the current user invocation still win. An older source
plan's prototype-only stop point does not override a current explicit end-to-end goal;
record it as historical scope and follow the current invocation.

Do not stop merely because the remaining steps are calibration, commit, push, ingestion,
or exact-SHA reconciliation. A final handoff that says "No commit, push, or calibration
rerun performed" is a failure unless a concrete stop condition prevented those actions.
When blocked, name the exact failed gate, command/result, authority or infrastructure
condition, and the next action; never present voluntary omission as completion.

## Logview Health Incident evidence and score acquisition

For `source_kind: logview-health-incident`, read
`references/logview_health_incident_evidence.md` completely before source acquisition,
trajectory retrieval, experiment-score interpretation, or repair. Follow its exact
Health Incident → Logview → Opsmate, ACE Muse/Codex, native Opsmate eval, completeness,
leak, provenance, `SYSTEM_ARM`, and `UNSCORABLE` contracts. Keep all raw records and IDs
author-only.

## Current review lessons

Treat these as regression checks, then refresh them from live exact-SHA reviews:

- Prefer typed causal facts and authoritative state over hidden prose keyword clusters.
- Run the Oracle and valid paraphrase/negation cases against the shipped grader after
  every grader edit; the Oracle must not fail the regex intended to accept it.
- Instructions state symptoms, interfaces, safety limits, outcomes, and report shape—not
  the deduction chain, root cause, remediation sequence, or the list of decoy answers.
- Audit privileged helpers for agent-writable paths, symlink traversal, interpreter
  replacement, and forged CTRF/reward artifacts.
- Avoid wall-clock proof windows and repeated one-shot/signed-snapshot scaffolds. Novelty
  must change the reasoning route and verifier architecture, not service nouns.
- Build a mechanical instruction-to-assertion matrix and pin every review to the full SHA.
- Treat every source-observed representation of one semantic fact as equivalent unless
  the public contract explicitly distinguishes them. Normalize typed aliases before
  comparison and regression-test each observed spelling; never let the Oracle's chosen
  spelling become a hidden requirement.
- An evidence family is required only when the public contract states a conclusion that
  genuinely requires that family. Do not promote the Oracle's endpoint route, internal
  family taxonomy, or minimum-read strategy into a secret grader contract.

## Approved-model instruction authorship

Read `references/first_party_generation.md` completely. `instruction.md` and every path
that current policy or provenance marks first-party-required must be authored by a real,
fresh K3 or Meta-owned Muse/MetaCode session. Codex orchestrates and reviews; it must not
silently write the candidate bytes, claim a session that never ran, or stop after a
failed launch. The authoring model must express the frozen contract, not redesign or
expand it. Missing verified first-party output blocks review, calibration, and push.

The authoring command must name the exact model explicitly. Before launch, capture the
current output of `metacode models meta` or `metacode models atlascloud` and select a
listed approved model. Never omit `--model`, rely on a provider default, treat
`--provider meta` as proof of model identity, or accept a launcher banner as an
authorship receipt. Export the completed session and mechanically verify that its
recorded provider and model ID exactly match the selected model. A run that resolves to
an unselected/default model (including a generic Muse Spark default) is invalid even if
the file looks correct.

When cloud provenance reports Codex write-log overlap for `instruction.md`, a K3
clean-room rewrite is mandatory (no repository helper exists — run it manually):
build the overlap corpus from every cloud `blocks[].text` span plus all available
Codex-authored contract/output transcripts, compare against the candidate file with
literal matching plus case/punctuation-normalized n-gram comparison (flag any
non-literal overlap beyond unavoidable public literals), and have K3 independently
reauthor the complete file from the frozen requirements brief without seeing the
flagged text. Codex must not patch even one character of the result. A
Meta-owned session receipt does not override an L3 `agentWrites: CONTAMINATED` verdict.

## Build and validation loop

Follow the `sev-to-codimango-task` quality lifecycle through implementation, verifier
hardening, no-op and adversarial controls, repeated Oracle, five valid Avocado trials on
unchanged task bytes, current ADO Deep Review, provenance/contamination/novelty checks,
commit, push, and exact-SHA reconciliation. Adapting this lifecycle never changes or
mislabels the source kind.

### Reviewer-feedback closure gate

For `repair-existing`, every reviewer comment is a required repair item, regardless of
severity or whether automated checks pass. Before editing, fetch all available human and
automated feedback: task reviews, comments, errors, exact-SHA full/deep reviews, trial
analyses, and author-validation reports. Do not rely on a summary when the underlying
finding is available.

1. Create one author-only reviewer-feedback ledger. Give every distinct finding a stable
   ID and record its source, reviewer, source SHA, exact text, affected requirement/file,
   severity, and whether it is current or stale.
2. Assign exactly one disposition: `OPEN`, `FIXED`, `NOT_APPLICABLE`, `SUPERSEDED`, or
   `EXTERNAL_BLOCKER`. `NOT_APPLICABLE` and `SUPERSEDED` require written evidence; they
   are not ways to dismiss inconvenient feedback.
3. For every `FIXED` finding, record the changed files, the smallest regression test that
   failed before or represents the reported case, its passing result after repair, and
   the broader downstream gates invalidated by the change. A code diff or green unrelated
   test is not proof of closure.
4. When feedback reports a valid solution rejected by wording, add the exact reported
   case as a passing regression and add nearby valid paraphrases plus adversarial
   negatives. Repair the grader/contract mismatch without weakening behavioral checks.
5. When feedback identifies a prompt-versus-grader mismatch, either make the public
   requirement explicit through the approved instruction-authoring route or accept every
   equivalent relevant behavior/evidence allowed by the existing instruction. Never keep
   a hidden stricter contract.
6. Re-read all feedback after every material repair and reconcile it against the current
   bytes. New or previously missed comments reopen the queue. Preserve stale findings and
   their dispositions rather than deleting history.
7. Before push, require zero `OPEN` findings, evidence-backed dispositions for every row,
   and a fresh full static review over the complete candidate. After push, fetch the
   exact-SHA review/comment state again and add any new findings before claiming readiness.

A prior reviewer decision of `revision` remains an outstanding external review state
until the repaired exact SHA is available for human re-review. Passing TBR or local tests
does not erase it. `READY_FOR_HUMAN_SUBMISSION` means every comment is locally resolved
with evidence and the candidate is ready to return to the reviewer; it does not claim
the reviewer has accepted it.

### Too-easy repair loop

In `repair-existing`, treat an Avocado `too easy` finding or three or more genuine passes
out of five as a mandatory redesign trigger, not a passing result and not a reason to
merely tighten the grader.

1. Re-open the source incident, causal timeline, mitigations, Opsmate and experiment
   trajectories/scores, prior trial patches, and exact-SHA review. Identify which
   reasoning dimensions the current task fails to exercise: temporal reconciliation,
   cross-component state, competing causal hypotheses, partial recovery, rollback
   safety, or verification of the final state.
2. Make the task harder by adding realistic coupled components, secondary symptoms,
   decoys, intermediate failure states, or recovery constraints that force more of the
   incident's causal structure to be investigated. Prefer source-backed details.
3. Synthetic or fictional additions are allowed only when they are a plausible extension
   of the same incident and core failure mode. Record each addition and its rationale in
   author-only evidence; never present invented details as source-incident facts, splice
   in a second incident, or change the task's identity.
4. Every added issue must be agent-visible, falsifiable, relevant to the final recovery,
   and exercised by the Oracle and grader. Supply reachable evidence that distinguishes
   the real cause from each decoy. Do not add arbitrary breakage, trivia, hidden facts,
   prose padding, brittle keyword checks, or unrelated components merely to lower pass
   rate.
5. Rebuild the instruction-to-assertion matrix, negative controls, adversarial controls,
   Oracle, static review, provenance/novelty checks, and approved-model instruction
   authorship when the contract changes. Then run a fresh five-trial batch on identical
   task bytes and classify every failure through the sandbox gate.
6. Repeat while the task remains at three or more genuine passes out of five, but stop
   if no fair, coherent extension exists. Never manufacture unfairness or claim readiness
   while calibration still marks the task `too easy`.

### Report-contract repair gate

When a review finds a brittle or under-enforced report grader, repair the contract and
the grader together. A state-correct Oracle is not sufficient when its report violates
the instruction or passes through a grader gap.

1. Build a report requirement matrix mapping every instruction requirement to a grader
   assertion, a positive test, a valid-paraphrase test, and a targeted negative or
   mutation test. Unmapped requirements block readiness.
2. Parse citations into exact evidence IDs and resolve them against evidence actually
   observed during the run. Reject invented IDs, case variants, arbitrary tokens that
   merely match a regex, and citations to evidence the agent never read.
3. Enforce coverage over the **cited** evidence set, not merely the observed set. Require
   at least one valid cited ID from every required family, such as fleet/inventory,
   history, incident, plan, and control evidence when those families are in the contract.
   Derive this family set from the public instruction-to-assertion matrix, never from the
   Oracle's read sequence. If equivalent endpoints can prove the same required fact,
   accept all of them through semantic mapping instead of listing the route in the prompt.
4. Enforce semantic requirements directly. Check exact rejection reasons, minimum counts
   such as inspecting at least two distinct plans, selected scope, recovery action, and
   other required conclusions. A number or keyword appearing anywhere in prose must not
   satisfy an unrelated requirement.
5. Prefer structured report fields or a real parser over keyword regexes. When free-form
   prose is required, test multiple valid phrasings and negated/adversarial variants so
   wording changes do not alter the underlying verdict.
6. Make the Oracle satisfy the literal instruction, including citing every required
   evidence family. Never weaken the instruction or grader to accommodate an incomplete
   Oracle report.
7. Ensure every report-contract test is invoked by the shipped `test.sh`. Run `test.sh`
   from a clean task environment and fail the review when a test file is orphaned or can
   pass only when executed separately.
8. After any report or grader repair, rerun the Oracle, valid paraphrases, forged-citation
   cases, missing-family cases, wrong-reason cases, minimum-count cases, negations, no-op
   controls, the spec-to-test matrix, and static review before calibration.

### Mandatory pre-push review

**REQUIRED SUB-SKILL:** Use `review-task-tbench-v2` and read its adjacent
`calibration/anchors.md`. Run it read-only against the complete candidate after every
material task change. It must read every task file, fill every mandatory preflight row,
build both directions of the spec⇄test matrix, audit cheat vectors and Docker `COPY`
chains, and return its calibrated verdict. Resolve every Critical/High and enough Medium
findings to reach `Accept` before pushing. Static `Accept` is necessary but does not
replace runtime controls or trial reproduction.

The review must not modify or persist inside the task package. If it proposes a revised
instruction, convert only its factual findings into the author-only requirements brief;
never copy its candidate prose. A fresh approved K3/Muse session must make any
`instruction.md` change, followed by a new authorship receipt and hash check.

The pre-push decision is fail-closed. A timeout, empty report, launcher exit without a
verdict, globally empty contamination snapshot, stale partition that cannot cover the
candidate, or unavailable novelty source is `EXTERNAL_BLOCKER`, never `Accept`, `CLEAN`,
or “no task-specific issue.” Record the command, run ID, last output, and retry result,
then stop before commit/push until every mandatory gate returns meaningful terminal
evidence. Oracle, calibration, manual inspection, or an older review cannot substitute.

Immediately before push, mechanically assert all of the following in `run_state.json`:

- every required gate names the exact frozen package SHA/hash and has a terminal result;
- static review is explicitly `Accept`, not inferred from silence;
- provenance, contamination, and novelty each contain usable evidence, not an empty or
  out-of-window dataset;
- the public instruction-to-assertion matrix has no grader-only evidence family, literal
  alias, endpoint, or read-order requirement;
- all source-observed aliases and equivalent evidence routes have passing regressions;
- the repair queue and reviewer-feedback ledger contain zero `OPEN` rows.
- `instruction.md` has an explicit approved model/provider/session receipt whose exported
  session identity matches the launch command; no default model was used;
- the manual historical-write and n-gram overlap preflight has zero non-literal
  Codex overlaps, including every span from the latest cloud L3 provenance evidence;
- local provenance/stylometry returned meaningful terminal evidence. Record clearly
  that local provenance cannot waive cloud L3 and that readiness still requires the
  new pushed SHA's cloud provenance verdict.

Any false or unknown row blocks push. User urgency does not convert a missing gate into
authorization to weaken or skip it.

Never push first merely to discover whether provenance passes when the local historical
write/overlap audit was skipped. If the current task already has a cloud provenance
failure, add it to the repair queue and complete the K3 clean-room rewrite
described in "Approved-model instruction authorship" before another
candidate push. After push, inspect provenance for that exact SHA before describing any
other pending validation as the only blocker. `agentWrites: CONTAMINATED` means the task
is not ready regardless of classifier, stylometry, Oracle, or structural results.

### Failed-trial sandbox gate

**REQUIRED SUB-SKILL:** Use `create-trial-sandbox` for every distinct failure class in
the five-trial calibration batch and for every ambiguous failure. Sandbox work is
diagnostic and must never read or edit `instruction.md`.

Two failures count as one class only when their recorded failure stage, reward, verifier
signal, and agent-output defect are demonstrably equivalent. Matching error text or
reward alone is insufficient; when uncertain, sandbox both.

The helper currently contains a retired artifact-download call. Predownload artifacts,
then use its supported API:

```bash
H=$(find ~/.claude/agent-market/plugins ~/.codex/agent-market/plugins -path '*/team-aai/skills/create-trial-sandbox/helpers/trial_sandbox.py' 2>/dev/null | head -n 1)
[ -n "$H" ] || { echo "trial_sandbox.py not found under agent-market plugins (team-aai plugin required)" >&2; exit 1; }
S="$AUTHOR_ONLY_DIR/trial-sandboxes/<trial-id>"
mkdir -p "$S/artifacts"
codimango trial artifacts <trial-id> --download "$S/artifacts"
python3 "$H" create --trial <trial-id> --task <task-dir> --dir "$S"
python3 "$H" test --dir "$S"
python3 "$H" reference --dir "$S"
```

Interpret results strictly:

- `ALIGN` reproduces the reward; it does not prove why.
- On `MISMATCH`, rebuild with replay and retest before classifying.
- `ENV SUSPECT` means task/harness setup is broken; fix it and invalidate that trial.
- `ALIGN` plus `ENV FAITHFUL` supports a genuine agent failure only after reviewing the
  reconstructed patch. A claimed cause requires the smallest `try --patch` change that
  flips reward and the sandbox skill's fresh independent audit verdict. Otherwise label
  the explanation conjecture.
- A persistent mismatch with a faithful reference is reported as the documented local
  reproduction ceiling, not silently counted as an agent failure. Exclude it from both
  the calibration numerator and denominator and obtain a replacement valid trial. Do not
  push until exactly five trials have valid classifications.

Keep sandbox artifacts, patches, fidelity reports, and hypotheses outside the task.
Use unique per-trial directories. After the final receipt, targeted cleanup may destroy
that sandbox's container/trial image while retaining review evidence; never run broad or
repository-wide Docker cleanup.

### One-candidate push gate

After the final static `Accept`, local author matrix, sandbox classifications, repeated
Oracle, calibration band, and quality/provenance/novelty checks all pass, record a task
package manifest/hash and freeze those bytes. Commit and push that candidate once. A
remote finding may justify another candidate, but diagnose it first and repeat the full
local review/sandbox/author-matrix gate before another push. Never use serial pushes as
the debugging loop.

Before pushing, resolve and record the repository's ingestion branch and how Codimango
discovers task updates. A push to a feature branch is not delivery when Codimango reads
the default branch. Do not report “pushed,” “synced,” or “ready” merely because
`git push` succeeded. After the push or authorized merge, prove all of the following:

- the frozen commit is reachable from the exact branch Codimango ingests;
- the remote branch resolves to, or contains, the expected full SHA;
- Codimango's `headCommitSha`, `validationCommitSha`, and task link no longer point only
  to the prior candidate;
- exact-SHA validation ran against the expected full SHA.

If a merge, pull request, or default-branch update is required but not authorized, stop
with `PUSHED_FEATURE_BRANCH_NOT_INGESTED`. Give the branch, commit, and required merge
action. Never imply that the task can be submitted from the stale Codimango revision.

Before readiness, verify the task's source/synthetic classification in both submitted
metadata and the live Codimango surface. The classification must match the source ledger
and the author's declared status. `Synthetic:UNKNOWN`, a missing classification, or a
disagreement between README, tags, source kind, and Codimango is a blocking metadata
error, not cosmetic UI text. Diagnose and correct the authoritative metadata field,
then re-ingest and verify the rendered classification. Never add a synthetic or
semi-synthetic label merely to suppress `UNKNOWN`, and never remove a truthful label
merely to obtain a desired display value.

- Treat each deep-review dimension independently; repair every current-package FAIL,
  Critical, or High finding even when the aggregate label passes.
- Difficulty target is one or two genuine Avocado passes out of five. Three or more passes
  is `too easy` and requires the difficulty repair loop; a 0/5 task first needs a
  fairness/grader audit.
- A push starts validation; do not queue a duplicate rerun. Under an end-to-end `/goal`,
  a necessary scoped rerun is authorized only for a stale, invalidated, missing, or
  infrastructure-failed result and must pin the expected full SHA. Never rerun a passing
  unchanged gate or use a bare full rerun when a narrow retry is available.
- Current unauthorized/Claude provenance requires clean-room reauthoring. Exactly one
  affected path uses the repository's one-path protocol; multiple or ambiguous paths
  require clean-room reauthoring of the complete affected set. Codex-only provenance is
  owner-accepted for files other than the newly required approved-model-authored
  `instruction.md`. Never hide authorship, label K3 as Meta-owned, or claim an authoring
  route without authoritative write logs.
- Freeze the package after substantive exact-SHA gates pass. Human acceptance/release is
  always the terminal decision.

## Completion receipt

Return: source kind and stable source key, task slug, repository and exact SHA, human
author identity, exact provider/model/session receipt for `instruction.md`, dedupe
evidence, local control matrix, trial classifications, deep-review dispositions,
provenance/contamination/novelty results, Codimango validation details, and any genuinely
external blocker. For a Logview task, also return the policy-verified origin marker and
the Opsmate/ACE Muse/Codex trajectory-and-score ledger, including every unavailable,
partial, leaked, expired, or unscorable arm and its exact reason.

The receipt must include the final fresh calibration trial/job IDs and classifications,
commit SHA, push confirmation, validation job for that exact SHA, and terminal result of
every required gate. Missing commit, push, calibration, or exact-SHA validation evidence
means the task is not ready unless the receipt identifies a genuine stop condition.
Push confirmation must identify the ingested remote branch and prove that Codimango is
showing the expected full SHA; a feature-branch-only push is incomplete. The receipt
must also record the final rendered source/synthetic classification, and any `UNKNOWN`
value blocks `READY_FOR_HUMAN_SUBMISSION`.

For `develop-draft` and `repair-existing`, completion additionally requires an empty repair queue, no stale
required receipt, zero `OPEN` reviewer-feedback findings, evidence-backed dispositions
for every reviewer comment, all required exact-SHA gates terminal and passing, and a
clear `READY_FOR_HUMAN_SUBMISSION` state in the author-only `run_state.json`. Do not
report completion merely because meaningful progress was made.

## Stop conditions

Stop rather than substitute when the source is inaccessible, already used, unsuitable,
cannot be made fair, requires incident splicing, lacks scoped mutation authority, or the
approved authoring surface is unavailable. Never silently choose a different problem.

# Developing an Idea-Only or Unregistered Task

Use this reference only for `mode=develop-draft`. The draft may be a directory, partial
package, source note, or basic mechanism idea. Missing downstream artifacts are expected.

Start persistent work with:

```text
/goal $oaoa-sev-task-autopilot
mode=develop-draft
source_kind=<sev or logview-health-incident>
draft=<absolute task path or author-only idea brief>

Develop the basic idea, compare a fair difficulty ladder, select one coherent target,
and continue through provenance, review, validation, calibration, commit, push, and
exact-SHA reconciliation until READY_FOR_HUMAN_SUBMISSION.
```

## 1. Inventory without inventing history

Record the source evidence, current idea, existing files, repository state, authorship
receipts, tests, reviews, experiments, calibration, and registry state. Mark each item
`PASS`, `FAIL`, `STALE`, `MISSING`, or `NOT_YET_APPLICABLE`. Never fabricate an old
receipt; generate fresh evidence for the current bytes.

## 2. Freeze the core

Before expanding the idea, freeze the source kind, stable incident key, causal mechanism,
capability being tested, observable recovery outcome, safety limits, and task identity.
Any change to this core requires explicit user confirmation. Added difficulty must deepen
the same problem rather than substitute another incident or task.

## 3. Generate an author-only option set

Derive possible extensions from evidence surfaces, coupled components, temporal ordering,
causal ambiguity, believable decoys, partial recovery, mutation scope, rollback safety,
and final-state proof. Label every option `SOURCE_BACKED` or `PLAUSIBLE_SYNTHETIC` and
record its rationale. Synthetic details must never be represented as incident facts.

## 4. Build a difficulty ladder

Define at least `baseline`, `target`, and `stretch` variants. For each, record:

- required reasoning and evidence;
- visible discriminators and falsifying evidence;
- likely wrong paths and why they are plausible;
- verifier and Oracle implications;
- fairness, leakage, novelty, and brittleness risks.

These are alternatives for choosing one task, not components that must all be bundled.

## 5. Select one coherent target

Choose the variant that best balances source fidelity, novelty, solvability, grader
robustness, and calibration value. Do not add arbitrary failures, hidden facts, unrelated
components, or prose padding merely to reduce pass rate. Preserve unused options only in
author-only notes for later tasks.

## 6. Establish the package and ledgers

Create or complete the canonical task package in a dedicated clean worktree. Outside the
submitted directory, create `run_state.json`, a source ledger, option/difficulty ledger,
spec-to-test matrix, provenance receipts, and repair queue. Register the task when the
normal lifecycle requires it; absence of an existing registry row is not completion.

## 7. Apply the full lifecycle

Use the parent skill's approved-model `instruction.md` authorship, provenance,
contamination, novelty, report-contract, Oracle, negative/adversarial control, review,
failed-trial, five-run calibration, commit, push, and exact-SHA gates. Apply the same
three-or-more-passes-out-of-five too-easy loop. Every material byte change invalidates
all affected downstream receipts.

## 8. Completion

Continue until one frozen, pushed exact SHA is `READY_FOR_HUMAN_SUBMISSION`. An idea,
local package, green Oracle, provenance pass, or partial calibration is progress only.
Human submission, acceptance, release, and landing remain separately authorized actions.

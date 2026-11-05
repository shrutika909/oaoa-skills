# First-Party File Generation

This is an execution gate, not advice. Use it for new tasks, developed drafts, repairs,
and provenance reauthoring.

## 1. Determine the required file set

Build an author-only manifest before launching a model. It always includes
`instruction.md`. Add every path that repository policy, current provenance results, or
the active validation contract explicitly requires to be first-party authored. Record
the reason per path. Do not broaden the set merely because a file is convenient to
delegate, and do not omit a provenance-flagged path.

For one affected path, use the repository's one-path clean-room protocol. For multiple
or ambiguous affected paths, reauthor the complete affected set together from the
first-party requirements, without showing the author flagged text.

## 2. Prepare clean-room inputs

Create an author-only requirements brief containing source-backed behavior, visible
interfaces, allowed actions, observable outcomes, safety limits, and public report
contract. It may identify the allowed output paths. It must not include old or rejected
task wording, deleted versions, model output, reviewer-only gold, hidden assertions, or
the answer.

Record pre-run hashes and working-tree state. Use a clean isolated worktree. The author
session may read the brief and task environment needed to produce the allowlisted files,
but must not inspect Git history or earlier versions of those files.

## 3. Freeze design before authorship

The first-party author is a constrained writer, not a task designer. Complete difficulty
design, evidence placement, decoys, verifier behavior, safety boundaries, and the public
contract before launch. Give the author an immutable requirements manifest with stable
requirement IDs and an explicit `MUST_NOT_ADD` list.

Known regression: a MetaCode rewrite exposed the investigation recipe and recovery
mechanics; Avocado then followed those instructions and passed 5/5. Treat this as public
answer leakage and `AUTHOR_SCOPE_CREEP`, not as evidence that the underlying task is easy.

The author must not add or change:

- task components, failure modes, recovery steps, success criteria, or report fields;
- hints, tutorials, suggested commands, investigation order, evidence locations, or the
  number and identity of relevant/decoy items unless the frozen public contract requires it;
- root cause, deduction chain, expected patch, hidden verifier logic, or Oracle behavior;
- extra examples or explanatory context that narrows the search space;
- easier alternatives, fallback paths, precomputed summaries, or new readable artifacts;
- any file outside the allowlist.

It may choose neutral wording and structure only. If the brief is insufficient or
inconsistent, it must report the gap without filling it creatively. When task design must
change, return to the design/difficulty phase, update the frozen manifest, invalidate
downstream receipts, and launch a new authoring session.

## 4. Launch a real approved author

Resolve availability at run time; never infer it from an old receipt.

- Meta-owned route: run `metacode models meta`, select a currently listed model, and
  launch a fresh Muse session. Prefer `meta/avocado-code-flex` only when listed.
- K3 route: confirm exact identity `atlascloud/moonshotai/kimi-k3` using
  `metacode models atlascloud`. K3 is approved for full authorship but is not Meta-owned,
  and its output requires human review.

For unattended task-scoped generation, prefer the Meta-owned route:

```bash
muse exec --json \
  --provider meta --model "$MODEL" \
  --workspace "$WORKTREE" \
  --worktree existing --worktree-existing "$WORKTREE" \
  --max-model-steps 20 --approval-mode on-request \
  --prompt-file "$AUTHOR_ONLY_PROMPT"
```

For K3, use the current interactive MetaCode surface:

```bash
METACODE_NON_META_ALLOWED=1 \
META_METACODE_REDIRECT_TO_MUSE=0 \
metacode --model atlascloud/moonshotai/kimi-k3
```

Do not use `--yolo`, disable approvals, or simulate first-party authorship with the
current Codex session. “In the background” means a genuine separate authoring session;
it does not permit bypassing approval or sandbox controls.

`--model` is mandatory. Do not use Muse's provider default, and do not infer the model
from a Meta provider banner. Save the model-list output used for selection. After the
run, export the durable session and verify its recorded `provider_id` and `model_id`
against the command. Any mismatch, omitted model, unavailable requested model, or
fallback/default resolution invalidates the run and requires a fresh author session.

The prompt must state: “Implement only the allowlisted files from the frozen requirement
IDs. Do not improve, expand, simplify, teach, or redesign the task. Do not add facts or
hints. If anything is missing, stop and report the missing requirement.”

## 5. Supervise failures instead of abandoning generation

Capture exit status, structured output, session ID, model identity, and changed paths.
If the launch or generation fails:

1. classify the failure as availability, authentication, approval, timeout, malformed
   prompt, wrong paths, empty output, or validation failure;
2. fix only the orchestration or requirements brief, never hand-write replacement bytes;
3. retry in a fresh session with the same frozen requirements;
4. if K3 cannot run non-interactively, use an available approved Meta-owned Muse model;
5. stop only when no approved route is available or repeated failures have a concrete
   external cause, and record the exact commands/results as a blocker.

A failed first attempt is not permission to skip generation. A text response from the
model is not success unless the required files were actually written.

## 6. Verify the write boundary and semantic contract

After every attempt:

- reject empty or placeholder output;
- reject any change outside the allowlisted paths;
- inspect every required file for leaked diagnosis, hidden gold, or copied wording;
- run the smallest syntax/contract checks relevant to those files;
- save model/provider, session ID, timestamps, changed-file set, and SHA-256 per file;
- ensure the final file bytes match the successful session's write set.

Build a requirement-ID-to-output matrix and compare the generated bytes with the frozen
manifest. Reject and regenerate when output contains an unmapped requirement, hint,
component, evidence disclosure, solution detail, or easier path—even if the prose is
otherwise high quality. Do not repair the model's scope creep by editing the file in
Codex; tighten the brief and run a fresh approved author.

Run an explicit recipe-leak review before trials. Fail the output if it reveals the
investigation sequence, names which evidence to correlate, tells the agent which
hypotheses to reject, identifies the faulty component, prescribes recovery mechanics,
or converts a discovery requirement into a checklist of solution steps. Public outcome,
safety, interface, and report-shape requirements are allowed; the route to satisfy them
must remain for the evaluated agent to discover.

After generation, rerun the difficulty/leakage review against the unchanged environment.
The generated public files must not reduce the investigation required by the selected
difficulty variant. If calibration becomes easier because the author exposed information,
classify it as `AUTHOR_SCOPE_CREEP`, reject the receipt, and regenerate before calibration.
Discard every trial produced from the leaked bytes. Only a fresh batch on the corrected,
hash-frozen candidate may count toward the one-or-two-passes-out-of-five target.

If a later edit changes any required file, its receipt is invalid. Regenerate that file
through a fresh approved session; Codex must not patch it directly, even for a small fix.
Verify the recorded hashes again against the committed blobs and final pushed SHA.

## 7. Downstream gate

Do not begin final static review or calibration until all required files have valid
receipts. Do not commit or push when a required path is missing, was written by Codex,
has an unverifiable session, or differs from its receipt. Include every receipt and any
failed-attempt history in the author-only run state and completion report.

Before commit or push, run the repository's historical Codex-write extractor and n-gram
overlap checker for every first-party-required path. Seed the corpus with all available
local writes, coordinator output, requirements summaries, and every span reported by
the latest cloud L3 provenance evidence. Only unavoidable public literals may remain.
If cloud reports `agentWrites: CONTAMINATED`, an otherwise valid Meta/K3 receipt is not
enough: use the repository K3 clean-room rewrite loop and obtain a new exact-SHA cloud
provenance result. Local stylometry cannot waive cloud write-log evidence.

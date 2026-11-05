#!/bin/sh
set -eu

root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
skill="$root/SKILL.md"
workflow="$root/references/workflow.md"

grep -q '^## Mandatory registry gate$' "$skill"
grep -q 'oaoa-evaluator.internalmeta.com/live/oaoa-task-registry' "$skill"
grep -q 'does not report `Incomplete`' "$skill"
grep -q 'all local and remote branch tips' "$skill"
grep -q 'Inspect the Knots authoring claim' "$skill"
grep -q 'Fail closed on an unavailable, denied, truncated, stale, or ambiguous registry' "$skill"
grep -q '^## 0. Clear the cross-author registry gate$' "$workflow"
grep -q 'Do not open trajectories or production query results until this phase' "$workflow"

echo "registry gate contract test passed"

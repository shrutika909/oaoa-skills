# OAOA Skills

Shareable OAOA SEV task-building skills. Anyone can copy these into their own
skills directory — no OD-specific paths.

## Skills

| Skill | Use when |
|---|---|
| `oaoa-sev-data-task-builder` | Creating one OAOA Terminal-Bench or SWE-Bench task from a named mitigated SEV, a Logview Health Incident task, or an authorized OpsMate experiment. Requires `benchmark=tbench\|swebench` + exactly one source. |
| `oaoa-sev-task-autopilot` | Developing / repairing an OAOA Terminal-Bench RCA task end-to-end until its exact SHA is `READY_FOR_HUMAN_SUBMISSION` (`new`, `develop-draft`, or `repair-existing` modes). |

## Install

Copy one or both skill folders into your skills directory:

```bash
# Codex
cp -r oaoa-sev-task-autopilot ~/.codex/skills/
cp -r oaoa-sev-data-task-builder ~/.codex/skills/

# Claude Code
cp -r oaoa-sev-task-autopilot ~/.claude/skills/
cp -r oaoa-sev-data-task-builder ~/.claude/skills/
```

Keep the two skills as siblings — `oaoa-sev-data-task-builder` references
`../oaoa-sev-task-autopilot/SKILL.md`.

## Requirements

- `oaoa-sev-task-autopilot` expects the `create-trial-sandbox` helper from the
  `team-aai` plugin (`~/.claude/agent-market/plugins/...`), resolved
  automatically at runtime.
- `oaoa-sev-data-task-builder`'s tbench branch optionally uses the personal
  `build-sev-query-databases` skill and the `codimango` ODS tooling checkout,
  only when the frozen task contract requires that evidence.

## Source

Ported from a personal OD (`~/.codex/skills`). Hardcoded OD paths were made
portable — see commit history for the mapping.

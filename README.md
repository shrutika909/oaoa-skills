# OAOA Skills

Shareable OAOA SEV task-building skills. Anyone can copy these into their own
skills directory — no OD-specific paths.

## Skills

| Skill | Use when |
|---|---|
| `oaoa-sev-data-task-builder` | Creating one OAOA Terminal-Bench or SWE-Bench task from a named mitigated SEV, a Logview Health Incident task, or an authorized OpsMate experiment. Requires `benchmark=tbench\|swebench` + exactly one source. |
| `oaoa-sev-task-autopilot` | Developing / repairing an OAOA Terminal-Bench RCA task end-to-end until its exact SHA is `READY_FOR_HUMAN_SUBMISSION` (`new`, `develop-draft`, or `repair-existing` modes). |
| `build-sev-query-databases` | **Bundled local-only dependency.** Builds the bounded offline query-database component (Scuba/Hive/Daiquery/Presto/LogView → SQLite replay). Invoked by the data-task-builder tbench branch when the frozen contract requires query-DB evidence. |

## Install

Copy the skill folders into your skills directory:

```bash
# Codex
cp -r oaoa-sev-task-autopilot oaoa-sev-data-task-builder build-sev-query-databases ~/.codex/skills/

# Claude Code
cp -r oaoa-sev-task-autopilot oaoa-sev-data-task-builder build-sev-query-databases ~/.claude/skills/
```

Keep the three folders as siblings — `oaoa-sev-data-task-builder` references
`../oaoa-sev-task-autopilot/SKILL.md` and `./build-sev-query-databases/SKILL.md`.

## Dependencies: bundled vs linked

**Bundled in this repo (was local-only):**
- `build-sev-query-databases/` — full skill: SKILL.md + 10 `references/` + `scripts/`
  (scaffold.py, scaffold_from_sev.py, synthetic_reconstruct.py, replay_server.py,
  client.py, discover_*.py, query-cli, tool_cli.py) + `tests/` + `assets/` +
  `examples/` + `man/`. No secrets found; tool specs are synthetic-simulated
  schemas; fixtures reference example SEV S707352 only.

**Already out there — clone/install, do not copy:**
- `codimango/oaoa-tbench` repo → `.agents/skills/sev-investigation-task/SKILL.md`
  and `.agents/skills/sev-to-codimango-task/SKILL.md` (+ its `references/` and
  `scripts/`) — required foundations for the autopilot.
- `codimango/oaoa-tbench` repo → `docs/reference/sev_to_synthetic_task_playbook.md`
  (main branch) — quality lifecycle reference.
- `codimango/swe-bench-aai-labs-oaoa` repo (102 tracked files) →
  `tooling/ods-tool/authoring/SKILL.md` (+ authoring/anonymization/data-model/
  packaging docs and scripts) — required when the frozen contract needs ODS
  counter/alert evidence. A bare SKILL.md copy is insufficient.
- `team-aai` plugin (install via marketplace) → `swebench-flow`,
  `create-trial-sandbox` (canonical sources in fbsource at
  `fbcode/claude-templates/components/plugins/team-aai/skills/`).
- `review-task-tbench-v2` — confirm which revision your `team-aai` install
  carries; canonical sources live under `team-aai-dev` / `team-aai/quality` in
  fbsource.
- `team-oaoa` plugin → `sev-to-tbench-task` (canonical source in fbsource at
  `fbcode/claude-templates/components/plugins/team-oaoa/skills/`).

**Unresolved — locate before relying on a fresh machine:**
- `k3-instruction-rewrite-loop` — referenced by the autopilot provenance gate but
  found in neither fbsource nor the oaoa-tbench repo. Resolve its source before
  trusting the clean-room rewrite gate elsewhere.

**Live systems (need access + identity, not bundlable):**
OAOA candidate registry + candidate sheet + cross-author registry, Knots
authoring claims, `codimango` CLI + task checkout, `meta` CLI + ACLs (SEV,
Logview, OpsMate, ACE, Scuba, quality-toolkit), `metacode`/`muse`, `fbpython`.

## Portability notes

- The two hardcoded author names (`Shrutika Naik, Akash Jothi`) are now marked
  as the default registry owners at time of writing — replace with the current
  author list from the registry before selecting on a new machine.
- The `trial_sandbox.py` lookup searches both `~/.claude` and `~/.codex`
  agent-market plugin paths.
- Originals under the author's `~/.codex/skills` still carry old absolute paths;
  this repo is the portable source of truth.

## Source

Ported from a personal OD (`~/.codex/skills`). Hardcoded OD paths were made
portable — see commit history for the mapping.

# build-sev-query-databases prototype

This portable skill builds only the offline database component for a SEV-based
task. It is intended to be appended to Chandra's parent scaffolding workflow.

## Test

Give the receiving Odie this folder, install it as a local skill, and use the
prompt in `examples/PROMPT_S707352.md`. No approval token is required.

The skill accepts any SEV. `S707352` is only the forwarding prompt example;
`tests/fixture` deliberately uses `S_FIXTURE_001` to verify the implementation
does not embed that SEV or its trajectories.

## Executable prototype

The authoring agent discovers the requested SEV evidence and stages it according
to `references/staging-contract.md`, or runs autonomous discovery directly:

```bash
fbpython scripts/scaffold_from_sev.py --sev <SEV_ID> --output <BUILD_DIR>
```

For prepared staging:

```bash
fbpython scripts/scaffold.py \
  --sev <SEV_ID> \
  --source <STAGING_DIR> \
  --output <BUILD_DIR> \
  --release-mode export
```

Run `sh tests/run_end_to_end.sh` for the generic fixture test. Production
acquisition remains in the trusted authoring environment; raw discovery is private
and the generated replay runtime has no production fallback.

## Design snapshot

- One shared SQLite database per task/SEV
- Scuba, Daiquery, Hive, Presto, and LogView supported; package only used tools
- Separate replay container with tool-specific read-only adapters
- Deterministic SQLite dump, replay/client startup scripts, Bash CLI, and Python client
- Tool-specific schema metadata, private ToolReceipts, and Longview output status
- 3 GB database budget and 4 GB total component ceiling
- 500 MB completion floor for real database tasks, with row count derived from
  original source cardinality and row width rather than a fixed quota;
  tiny fixtures are contract tests only
- Production-like cardinality, skew, missingness, retries, duplicates, and
  background evidence are preserved instead of over-normalized away
- Private build report and evidence manifest; no answer leakage to the task
- SQLite is the MVP; DuckDB/Parquet is deferred until measured need

ToolSim is a design reference only and is not a runtime dependency.

## Complete T-Bench tasks

This tool stops at a validated query-replay component. For a complete OAOA
Terminal-Bench task, pass `scaffolding_summary.json` to
`oaoa-sev-task-autopilot` in `develop-draft` mode. The autopilot supplies
the remaining task design, instruction, non-database evidence, recovery
surface, oracle, grader, controls, calibration, reviews, push, and exact-SHA
validation. See `references/autopilot-integration.md`.

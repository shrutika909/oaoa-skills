# Test prompt for S707352

Use the installed `build-sev-query-databases` skill for `S707352`. Automatically
discover the relevant OpsMate experiments, custom trajectories, harnesses, and
cutoffs. I approve materialization for this test.

Build and validate the complete database scaffolding: acquire sufficient needed
and realistic unwanted evidence, skip documented duplicates, normalize the
trajectory formats, create the shared SQLite database, build the separate replay
container and tool-specific read-only adapters, and generate the man pages and
all required artifacts.

Do not expose private evidence or answers to the solving agent. At completion,
show the agent-safe scaffolding summary and tell me where the private
`build_report.md` was written. Analyze that report and identify any construction
defects, lost invariants, missing evidence, privacy risks, or unrealistic tool
behavior. Do not reveal its private contents to the task-solving agent.

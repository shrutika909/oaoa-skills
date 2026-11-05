#!/bin/sh
set -eu

root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)

test -s "$root/SKILL.md"
test -s "$root/examples/PROMPT_S707352.md"
test -s "$root/references/workflow.md"
test -s "$root/references/output-contract.md"
test -s "$root/references/staging-contract.md"
test -s "$root/references/logview-contract.md"
test -s "$root/references/anonymization-contract.md"
test -s "$root/assets/anonymization-policy.json"
test -s "$root/scripts/synthetic_reconstruct.py"
test -s "$root/tests/run_synthetic_reconstruction.sh"
test -s "$root/scripts/scaffold.py"
test -s "$root/scripts/scaffold_from_sev.py"
test -s "$root/scripts/discover_opsmate.py"
test -s "$root/scripts/tool_cli.py"
test -s "$root/scripts/replay_server.py"
test -s "$root/scripts/client.py"
test -s "$root/tests/run_end_to_end.sh"
test -s "$root/tests/run_container_end_to_end.sh"
jq -e . "$root/assets/private_authoring_manifest.example.json" >/dev/null
jq -e . "$root/assets/scaffolding_summary.example.json" >/dev/null
jq -e . "$root/assets/anonymization-policy.json" >/dev/null
jq -e . "$root/tests/fixture/synthetic_spec.json" >/dev/null
for tool in scuba hive daiquery presto logview; do
  jq -e . "$root/assets/tool_specs/$tool.json" >/dev/null
done

awk 'BEGIN {ok=0} /scenario\.sql/ {ok=1} END {exit !ok}' "$root/SKILL.md"
awk 'BEGIN {ok=0} /sevmate_sev_stakeholders_intern_tool_activity/ {ok=1} END {exit !ok}' "$root/references/workflow.md"
awk 'BEGIN {ok=0} /five ToolSpecs/ {ok=1} END {exit !ok}' "$root/references/output-contract.md"

echo "portable skill package is structurally valid"

#!/bin/sh
set -eu

root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
out=$(mktemp -d)
trap 'rm -rf "$out"' EXIT

fbpython "$root/scripts/synthetic_reconstruct.py" \
  --spec "$root/tests/fixture/synthetic_spec.json" \
  --policy "$root/assets/anonymization-policy.json" \
  --output "$out/staging" >/dev/null

fbpython "$root/scripts/scaffold.py" \
  --sev S_SYNTHETIC_001 \
  --source "$out/staging" \
  --output "$out/build" \
  --release-mode export

test -s "$out/build/replay/scenario.sqlite"
test -s "$out/build/replay/scenario.sql"
test -s "$out/build/private/build_report.md"
test -s "$out/build/private/private_authoring_manifest.json"
test -s "$out/build/private/anonymization_mapping.md"
test -s "$out/build/private/database_mapping.md"
test -s "$out/build/scaffolding_summary.json"
test -s "$out/build/task/contracts/logview.json"
test ! -e "$out/build/task/scenario.sqlite"
test ! -e "$out/build/task/scenario.sql"
test ! -e "$out/build/task/replay_server.py"

REPLAY_TOKEN=test-only-token RECEIPTS_PATH="$out/receipts.jsonl" fbpython "$out/build/replay/replay_server.py" \
  --db "$out/build/replay/scenario.sqlite" \
  --contracts "$out/build/replay/contracts" \
  --receipts "$out/receipts.jsonl" \
  --host 127.0.0.1 \
  --port 18080 >"$out/server.log" 2>&1 &
server_pid=$!
trap 'kill "$server_pid" 2>/dev/null || true; rm -rf "$out"' EXIT

ready=0
attempt=0
while [ "$attempt" -lt 50 ]; do
  if REPLAY_TOKEN=test-only-token "$out/build/task/bin/scuba" --endpoint http://127.0.0.1:18080 resources >"$out/resources.json" 2>/dev/null; then
    ready=1
    break
  fi
  attempt=$((attempt + 1))
  sleep 0.1
done
test "$ready" -eq 1

REPLAY_TOKEN=test-only-token "$out/build/task/bin/scuba" \
  --endpoint http://127.0.0.1:18080 \
  query --query-id fictional_event_window --limit 10 >"$out/query.json"

REPLAY_TOKEN=test-only-token "$out/build/task/bin/logview" \
  --endpoint http://127.0.0.1:18080 \
  mid_trend --query-id fictional_failure_chain \
  --filter mid=identity_000001 --limit 10 >"$out/logview-query.json"

kill "$server_pid"
wait "$server_pid" 2>/dev/null || true

jq -e '(.rows | length) == 4 and .complete == true and .next_page_token == null' "$out/query.json" >/dev/null
jq -e '.rows | length == 3' "$out/logview-query.json" >/dev/null
jq -e '.operations | index("mid_trend") != null' "$out/build/task/contracts/logview.json" >/dev/null
jq -e '.status == "passed" and .export_eligible == true' "$out/build/scaffolding_summary.json" >/dev/null
jq -e '
  .validation.checks.over_normalization.status == "passed" and
  .validation.checks.agent_cheating_surface.status == "passed" and
  .validation.checks.source_lineages_preserved.status == "passed" and
  .validation.checks.technical_invariants_declared.status == "passed"
' "$out/build/scaffolding_summary.json" >/dev/null
jq -e '
  .evidence_mix.bullseye == {"private_classes":["causal"],"row_count":7,"source_count":2} and
  .evidence_mix.supporting == {"private_classes":["supporting"],"row_count":4,"source_count":1} and
  .evidence_mix.directional == {"private_classes":["directional"],"row_count":4,"source_count":1} and
  .evidence_mix.misleading == {"private_classes":["competing","negative"],"row_count":8,"source_count":2}
' "$out/build/scaffolding_summary.json" >/dev/null
jq -e '
  .parent_handoff.component_scope == "offline_query_replay" and
  .parent_handoff.full_task_status == "not_built" and
  .parent_handoff.required_parent_skill == "oaoa-sev-task-autopilot" and
  .parent_handoff.required_parent_mode == "develop-draft" and
  .parent_handoff.ready_for_parent == true
' "$out/build/scaffolding_summary.json" >/dev/null
jq -e '
  (has("sev_id") | not) and
  (has("discovery") | not) and
  (has("database") | not) and
  (has("parent_handoff") | not) and
  ([.files[].path | startswith("task/")] | all)
' "$out/build/task/component_manifest.json" >/dev/null
test "$(sqlite3 "$out/build/replay/scenario.sqlite" "SELECT type FROM pragma_table_info('scuba__fictional_event_window') WHERE name='latency_ms';")" = "INTEGER"
test "$(sqlite3 "$out/build/replay/scenario.sqlite" "SELECT COUNT(*) FROM query_catalog WHERE tool='scuba';")" = "2"
test "$(sqlite3 "$out/build/replay/scenario.sqlite" "SELECT COUNT(DISTINCT table_name) FROM query_catalog WHERE tool='scuba';")" = "2"
if grep -R -E 'prod_service_42|ace_eval_events|devmate_events' "$out/build/task" "$out/build/replay" >/dev/null; then
  echo "production identifier leaked into reconstructed output" >&2
  exit 1
fi
test -s "$out/receipts.jsonl"

grep -q 'Source-to-table mapping' "$out/build/private/database_mapping.md"
grep -q 'SQLite declared type' "$out/build/private/database_mapping.md"
grep -q 'Private evidence mix' "$out/build/private/database_mapping.md"

echo "end-to-end scaffold, replay query, and receipt test passed"

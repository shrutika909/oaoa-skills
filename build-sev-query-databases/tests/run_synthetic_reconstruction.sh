#!/bin/sh
set -eu

root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
out=$(mktemp -d)
trap 'rm -rf "$out"' EXIT

fbpython "$root/scripts/synthetic_reconstruct.py" \
  --spec "$root/tests/fixture/synthetic_spec.json" \
  --policy "$root/assets/anonymization-policy.json" \
  --output "$out/staging"

jq -e '.release_eligible == true' "$out/staging/synthetic_reconstruction_report.json" >/dev/null
test "$(jq -r '.tool' "$out/staging/sources/fictional_event_window.json")" = "scuba"
test "$(jq -r '.tool' "$out/staging/sources/fictional_partitioned_jobs.json")" = "hive"
test "$(jq -r '.tool' "$out/staging/sources/fictional_orders.json")" = "daiquery"
test "$(jq -r '.tool' "$out/staging/sources/fictional_dependency_summary.json")" = "presto"
test "$(jq -r '.tool' "$out/staging/sources/fictional_failure_chain.json")" = "logview"

fbpython "$root/scripts/scaffold.py" \
  --sev S_SYNTHETIC_001 \
  --source "$out/staging" \
  --output "$out/build" \
  --release-mode export

jq -e '.export_eligible == true and .status == "passed" and (.known_gaps | length == 0)' "$out/build/scaffolding_summary.json" >/dev/null
test "$(sqlite3 "$out/build/replay/scenario.sqlite" 'SELECT COUNT(DISTINCT tool) FROM query_catalog;')" -eq 5
test "$(sqlite3 "$out/build/replay/scenario.sqlite" 'SELECT worker_id FROM hive__fictional_partitioned_jobs LIMIT 1;')" = "worker_000001"
test ! -e "$out/build/task/scenario.sqlite"

if fbpython "$root/scripts/scaffold.py" \
  --sev S_FIXTURE_001 \
  --source "$root/tests/fixture" \
  --output "$out/rejected" \
  --release-mode export >/dev/null 2>&1; then
  echo "export mode accepted non-synthetic input" >&2
  exit 1
fi

echo "synthetic reconstruction and export gate test passed"

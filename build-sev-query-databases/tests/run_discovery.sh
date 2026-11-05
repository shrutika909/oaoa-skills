#!/bin/sh
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
out=$(mktemp -d)
trap 'rm -rf "$out"' EXIT
fbpython "$root/scripts/discover_opsmate.py" --sev S_TEST --fixture "$root/tests/fixture/opsmate_discovery.json" --output "$out" >/dev/null
jq -e '.status == "complete" and (.database_calls | length) == 5 and (.missing_tools | length) == 0' "$out/source_inventory.json" >/dev/null
test "$(find "$out/private_calls" -type f | wc -l)" -eq 5
test "$(find "$out/trajectories" -type f | wc -l)" -eq 2
echo "OpsMate discovery test passed"

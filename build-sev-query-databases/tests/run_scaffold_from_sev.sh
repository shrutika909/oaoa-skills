#!/bin/sh
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
out=$(mktemp -d)
trap 'rm -rf "$out"' EXIT
fbpython "$root/scripts/scaffold_from_sev.py" --sev S_TEST --discovery-fixture "$root/tests/fixture/opsmate_discovery.json" --output "$out/build" >/dev/null
jq -e '.status == "passed" and .export_eligible == true and (.included_tools | length) == 5' "$out/build/scaffolding_summary.json" >/dev/null
test -s "$out/build/private/discovery/source_inventory.json"
test ! -e "$out/build/task/private"
echo "autonomous SEV scaffold test passed"

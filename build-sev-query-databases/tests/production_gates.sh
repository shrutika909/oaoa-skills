#!/bin/sh
set -eu

root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

for name in first second; do
  fbpython "$root/scripts/scaffold.py" \
    --sev S_FIXTURE_001 \
    --source "$root/tests/fixture" \
    --output "$tmp/$name" \
    --approve-materialization >/dev/null
done

test "$(sha256sum "$tmp/first/replay/scenario.sqlite" | cut -d' ' -f1)" = \
  "$(sha256sum "$tmp/second/replay/scenario.sqlite" | cut -d' ' -f1)"
test "$(sha256sum "$tmp/first/replay/scenario.sql" | cut -d' ' -f1)" = \
  "$(sha256sum "$tmp/second/replay/scenario.sql" | cut -d' ' -f1)"

test ! -e "$tmp/first/agent/scenario.sqlite"
test ! -e "$tmp/first/agent/scenario.sql"
test ! -e "$tmp/first/agent/private"
test -s "$tmp/first/validation_report.json"
(cd "$tmp/first" && sha256sum -c checksums.sha256 >/dev/null)
jq -e '.status == "passed" and (.checks | to_entries | all(.value == true))' \
  "$tmp/first/validation_report.json" >/dev/null

if LC_ALL=C grep -R -E 'classification_reason|prod_service_42|causal|directional' \
  "$tmp/first/agent" >/dev/null 2>&1; then
  echo "private evidence leaked into agent package" >&2
  exit 1
fi

if fbpython "$root/scripts/scaffold.py" \
  --sev S_FIXTURE_001 --source "$root/tests/fixture" --output "$tmp/first" \
  --approve-materialization >/dev/null 2>&1; then
  echo "existing output was overwritten" >&2
  exit 1
fi

echo "production gates passed"

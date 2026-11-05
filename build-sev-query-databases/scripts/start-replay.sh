#!/bin/sh
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
receipts=${RECEIPTS_PATH:-/private/receipts/tool_receipts.jsonl}
exec python3 "$root/replay_server.py" --db "$root/scenario.sqlite" --contracts "$root/contracts" --receipts "$receipts" --host "${REPLAY_HOST:-127.0.0.1}" --port "${REPLAY_PORT:-8080}"

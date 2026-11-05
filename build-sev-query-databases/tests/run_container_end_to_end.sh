#!/bin/sh
set -eu

root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
test_root=$(mktemp -d)
project="sev_scaffold_test_$$"
token="container-test-token"
port=$(fbpython -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1]); s.close()')
compose="$test_root/build/replay/compose.yaml"

cleanup() {
  if [ -e "$compose" ]; then
    REPLAY_TOKEN="$token" REPLAY_PORT="$port" COMPOSE_PROJECT_NAME="$project" \
      docker compose -f "$compose" down -v >/dev/null 2>&1 || true
  fi
  rm -rf "$test_root"
}
trap cleanup EXIT

fbpython "$root/scripts/synthetic_reconstruct.py" \
  --spec "$root/tests/fixture/synthetic_spec.json" \
  --policy "$root/assets/anonymization-policy.json" \
  --output "$test_root/staging" >/dev/null

fbpython "$root/scripts/scaffold.py" \
  --sev S_SYNTHETIC_001 \
  --source "$test_root/staging" \
  --output "$test_root/build" \
  --release-mode export

REPLAY_TOKEN="$token" REPLAY_PORT="$port" COMPOSE_PROJECT_NAME="$project" \
  docker compose -f "$compose" up -d --build

container_id=$(REPLAY_TOKEN="$token" REPLAY_PORT="$port" COMPOSE_PROJECT_NAME="$project" \
  docker compose -f "$compose" ps -q replay)
image_id=$(REPLAY_TOKEN="$token" REPLAY_PORT="$port" COMPOSE_PROJECT_NAME="$project" \
  docker compose -f "$compose" images -q replay)
task_image="${project}-task"
docker build -q -t "$task_image" -f "$test_root/build/task/Dockerfile.task" "$test_root/build/task" >/dev/null
test -n "$container_id"
test -n "$image_id"

ready=0
attempt=0
while [ "$attempt" -lt 50 ]; do
  if docker run --rm --network host --entrypoint python3 "$task_image" -c \
    "import urllib.request; r=urllib.request.Request('http://127.0.0.1:$port/v1/scuba/resources',headers={'Authorization':'Bearer $token'}); urllib.request.urlopen(r,timeout=2).read()" \
    >/dev/null 2>&1; then
    ready=1
    break
  fi
  attempt=$((attempt + 1))
  sleep 0.1
done
test "$ready" -eq 1

docker run --rm --network host --entrypoint python3 "$task_image" -c \
  "import json,urllib.request; body=json.dumps({'query_id':'fictional_event_window','limit':10}).encode(); r=urllib.request.Request('http://127.0.0.1:$port/v1/scuba/query',data=body,headers={'Authorization':'Bearer $token','Content-Type':'application/json'}); data=json.loads(urllib.request.urlopen(r,timeout=5).read()); assert len(data['rows']) == 4"

docker run --rm --network host --entrypoint python3 "$task_image" -c \
  "import http.client; c=http.client.HTTPConnection('127.0.0.1',$port,timeout=5); c.request('GET','/v1/scuba/resources',headers={'Authorization':'Bearer wrong'}); assert c.getresponse().status == 403"

docker run --rm --network host --entrypoint python3 "$task_image" -c \
  "import http.client; c=http.client.HTTPConnection('127.0.0.1',$port,timeout=5); c.request('POST','/v1/scuba/query',body=b'{bad',headers={'Authorization':'Bearer $token','Content-Type':'application/json'}); assert c.getresponse().status == 400"

docker exec "$container_id" python3 -c \
  "import json,pathlib; rows=[json.loads(line) for line in pathlib.Path('/private/receipts/tool_receipts.jsonl').read_text().splitlines()]; statuses={row['status'] for row in rows}; assert {'complete','denied','failed'} <= statuses"

docker inspect "$container_id" | jq -e \
  '.[0].Mounts | length == 1 and .[0].Destination == "/private/receipts"' >/dev/null

docker run --rm --entrypoint sh "$task_image" -c \
  'test ! -e /task/scenario.sqlite && test ! -e /task/scenario.sql && test ! -e /task/replay_server.py && test ! -e /private'

echo "separate-container replay, private receipt volume, and receipt coverage passed"

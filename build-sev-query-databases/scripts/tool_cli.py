#!/usr/bin/env fbpython
"""Tool-specific client entrypoint for an offline SEV replay."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


def call(endpoint: str, tool: str, operation: str, body: dict | None = None) -> None:
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(
        f"{endpoint}/v1/{tool}/{operation}",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.environ.get('REPLAY_TOKEN', '')}",
            "X-Replay-Identity": os.environ.get("REPLAY_IDENTITY", "simulated_oncall"),
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            print(response.read().decode())
    except urllib.error.HTTPError as error:
        print(error.read().decode(), file=sys.stderr)
        raise SystemExit(4)


def main() -> None:
    tool = Path(sys.argv[0]).name
    spec_path = Path(__file__).resolve().parent.parent / "contracts" / f"{tool}.json"
    spec = json.loads(spec_path.read_text())
    parser = argparse.ArgumentParser(prog=tool, description=spec["description"])
    parser.add_argument("--endpoint", default="http://127.0.0.1:8080")
    sub = parser.add_subparsers(dest="operation", required=True)
    sub.add_parser("resources")
    for operation in spec["operations"]:
        command = sub.add_parser(operation)
        command.add_argument("--query-id", required=True)
        command.add_argument("--limit", type=int, default=spec["limits"]["default_rows"])
        command.add_argument("--page-token")
        command.add_argument("--start-time", type=int)
        command.add_argument("--end-time", type=int)
        command.add_argument("--timeout-ms", type=int)
        command.add_argument("--filter", action="append", default=[])
    args = parser.parse_args()
    if args.operation == "resources":
        call(args.endpoint, tool, "resources")
        return
    filters = {}
    for item in args.filter:
        if "=" not in item:
            raise SystemExit("--filter must use column=value")
        key, value = item.split("=", 1)
        filters[key] = value
    call(
        args.endpoint,
        tool,
        args.operation,
        {
            "query_id": args.query_id,
            "limit": args.limit,
            "page_token": args.page_token,
            "start_time": args.start_time,
            "end_time": args.end_time,
            "timeout_ms": args.timeout_ms,
            "filters": filters,
        },
    )


if __name__ == "__main__":
    main()

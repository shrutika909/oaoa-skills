#!/usr/bin/env fbpython
"""Client for the generated read-only query replay service."""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request


def call(url: str, body: dict | None = None) -> None:
    encoded = json.dumps(body).encode() if body is not None else None
    token = os.environ.get("REPLAY_TOKEN", "")
    request = urllib.request.Request(
        url,
        data=encoded,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
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
    parser = argparse.ArgumentParser(prog="query-cli")
    parser.add_argument("--endpoint", default="http://127.0.0.1:8080")
    sub = parser.add_subparsers(dest="command", required=True)
    resources = sub.add_parser("resources")
    resources.add_argument("--tool", required=True)
    query = sub.add_parser("query")
    query.add_argument("--tool", required=True)
    query.add_argument("--query-id", required=True)
    query.add_argument("--limit", type=int, default=100)
    query.add_argument("--start-time", type=int)
    query.add_argument("--end-time", type=int)
    query.add_argument("--timeout-ms", type=int)
    query.add_argument("--filter", action="append", default=[])
    args = parser.parse_args()
    if args.command == "resources":
        call(f"{args.endpoint}/v1/{args.tool}/resources")
    else:
        filters = {}
        for item in args.filter:
            if "=" not in item:
                raise SystemExit("--filter must use column=value")
            key, value = item.split("=", 1)
            filters[key] = value
        call(
            f"{args.endpoint}/v1/{args.tool}/query",
            {
                "query_id": args.query_id,
                "limit": args.limit,
                "start_time": args.start_time,
                "end_time": args.end_time,
                "timeout_ms": args.timeout_ms,
                "filters": filters,
            },
        )


if __name__ == "__main__":
    main()

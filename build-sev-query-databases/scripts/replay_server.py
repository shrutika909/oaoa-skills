#!/usr/bin/env fbpython
"""Read-only replay service for a generated scenario database."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import ipaddress
import json
import os
import secrets
import socket
import sqlite3
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


class Handler(BaseHTTPRequestHandler):
    db: Path
    receipts: Path
    token: str
    receipt_lock = threading.Lock()
    snapshot_hash: str
    contracts: dict[str, dict[str, Any]]

    def authorized(self) -> bool:
        supplied = self.headers.get("Authorization", "").removeprefix("Bearer ")
        return bool(self.token) and secrets.compare_digest(supplied, self.token)

    def identity(self) -> str:
        return self.headers.get("X-Replay-Identity", "simulated_oncall")

    def send_json(self, status: int, payload: Any) -> None:
        body = json.dumps(payload, sort_keys=True).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def write_receipt(
        self,
        started: float,
        request_hash: str,
        status: str,
        count: int = 0,
        tool: str | None = None,
        operation: str | None = None,
        complete: bool | None = None,
    ) -> None:
        receipt = {
            "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
            "request_hash": request_hash,
            "status": status,
            "row_count": count,
            "elapsed_ms": round((time.time() - started) * 1000, 3),
            "tool": tool,
            "operation": operation,
            "identity": self.identity(),
            "snapshot_sha256": self.snapshot_hash,
            "completeness": complete,
            "receipt_schema_version": "1.0",
        }
        self.receipts.parent.mkdir(parents=True, exist_ok=True)
        with self.receipt_lock:
            with self.receipts.open("a") as handle:
                handle.write(json.dumps(receipt, sort_keys=True) + "\n")

    def do_GET(self) -> None:
        started = time.time()
        route = urlparse(self.path).path
        request_hash = hashlib.sha256(f"GET {route}".encode()).hexdigest()
        if route == "/health":
            self.send_json(200, {"status": "ok"})
            return
        if not self.authorized():
            self.write_receipt(started, request_hash, "denied")
            self.send_json(403, {"error": "denied"})
            return
        parts = route.strip("/").split("/")
        if len(parts) == 3 and parts[0] == "v1" and parts[2] == "resources":
            tool = parts[1]
            if tool not in self.contracts:
                self.write_receipt(started, request_hash, "unsupported", tool=tool, operation="resources")
                self.send_json(404, {"error": "unsupported_tool"})
                return
            if self.identity() not in self.contracts[tool].get("allowed_identities", []):
                self.write_receipt(started, request_hash, "denied", tool=tool, operation="resources")
                self.send_json(403, {"error": "denied"})
                return
            with sqlite3.connect(f"file:{self.db}?mode=ro", uri=True) as connection:
                rows = connection.execute(
                    "SELECT query_id, resource_name, metadata_json FROM query_catalog WHERE tool=? ORDER BY query_id",
                    (tool,),
                ).fetchall()
            self.write_receipt(started, request_hash, "complete", len(rows), tool, "resources", True)
            self.send_json(200, {"tool": tool, "resources": [{"query_id": r[0], "name": r[1], "metadata": json.loads(r[2])} for r in rows]})
            return
        self.write_receipt(started, request_hash, "unsupported")
        self.send_json(404, {"error": "unsupported"})

    def do_POST(self) -> None:
        started = time.time()
        raw = self.rfile.read(min(int(self.headers.get("Content-Length", "0")), 1_000_000))
        request_hash = hashlib.sha256(raw).hexdigest()
        status = "failed"
        count = 0
        code = 400
        payload: Any = {"error": "malformed"}
        if not self.authorized():
            self.write_receipt(started, request_hash, "denied")
            self.send_json(403, {"error": "denied"})
            return
        try:
            request = json.loads(raw or b"{}")
            parts = urlparse(self.path).path.strip("/").split("/")
            if len(parts) != 3 or parts[0] != "v1":
                raise ValueError("unsupported")
            tool = parts[1]
            operation = parts[2]
            contract = self.contracts.get(tool)
            if contract is None or operation not in contract["operations"]:
                code, payload, status = 404, {"error": "unsupported_operation"}, "unsupported"
                raise LookupError
            if self.identity() not in contract.get("allowed_identities", []):
                code, payload, status = 403, {"error": "denied"}, "denied"
                raise LookupError
            maximum_rows = int(contract["limits"]["max_rows"])
            limit = max(1, min(int(request.get("limit", contract["limits"]["default_rows"])), maximum_rows))
            with sqlite3.connect(f"file:{self.db}?mode=ro", uri=True) as connection:
                catalog = connection.execute(
                    "SELECT table_name, metadata_json, operation FROM query_catalog WHERE tool=? AND query_id=?",
                    (tool, request.get("query_id")),
                ).fetchone()
                if not catalog:
                    code, payload, status = 404, {"error": "resource_not_found_or_denied"}, "denied"
                else:
                    metadata = json.loads(catalog[1])
                    if catalog[2] != operation:
                        code, payload, status = 404, {"error": "unsupported_operation"}, "unsupported"
                        raise LookupError
                    time_range = metadata.get("time_range", {})
                    start = request.get("start_time")
                    end = request.get("end_time")
                    minimum = time_range.get("baseline_start")
                    maximum = time_range.get("cutoff")
                    if int(request.get("limit", contract["limits"]["default_rows"])) > maximum_rows:
                        code, payload, status = 422, {"error": "limit_exceeded"}, "limited"
                    elif request.get("timeout_ms") is not None and int(request["timeout_ms"]) <= 0:
                        code, payload, status = 408, {"error": "timed_out"}, "timed_out"
                    elif (start is not None and minimum is not None and int(start) < int(minimum)) or (end is not None and maximum is not None and int(end) > int(maximum)):
                        code, payload, status = 422, {"error": "outside_snapshot"}, "outside_snapshot"
                    else:
                        columns = [row[1] for row in connection.execute(f'PRAGMA table_info("{catalog[0]}")')]
                        timestamp_columns = [
                            str(column.get("name"))
                            for column in metadata.get("columns", [])
                            if isinstance(column, dict)
                            and str(column.get("type", "")).lower() == "timestamp"
                            and str(column.get("name")) in columns
                        ]
                        time_column = "time" if "time" in columns else (
                            timestamp_columns[0] if timestamp_columns else None
                        )
                        clauses = []
                        parameters: list[Any] = []
                        if time_column is not None and start is not None:
                            clauses.append(f'"{time_column}" >= ?')
                            parameters.append(int(start))
                        if time_column is not None and end is not None:
                            clauses.append(f'"{time_column}" <= ?')
                            parameters.append(int(end))
                        filters = request.get("filters") or {}
                        if not isinstance(filters, dict):
                            raise ValueError("filters must be an object")
                        for column, value in sorted(filters.items()):
                            if column not in columns:
                                raise ValueError("unknown filter column")
                            clauses.append(f'"{column}" = ?')
                            parameters.append(value)
                        where = " WHERE " + " AND ".join(clauses) if clauses else ""
                        page_token = request.get("page_token")
                        try:
                            offset = 0 if page_token in (None, "") else int(page_token)
                        except (TypeError, ValueError):
                            raise ValueError("invalid page token")
                        if offset < 0:
                            raise ValueError("invalid page token")
                        order_column = time_column or "rowid"
                        parameters.extend((limit + 1, offset))
                        rows = connection.execute(
                            f'SELECT * FROM "{catalog[0]}"{where} ORDER BY "{order_column}" ASC, rowid ASC LIMIT ? OFFSET ?',
                            parameters,
                        ).fetchall()
                        has_more = len(rows) > limit
                        rows = rows[:limit]
                        count = len(rows)
                        code, payload, status = 200, {
                            "columns": columns,
                            "rows": rows,
                            "complete": not has_more,
                            "next_page_token": str(offset + limit) if has_more else None,
                        }, "complete_empty" if count == 0 else "complete"
        except LookupError:
            pass
        except (ValueError, json.JSONDecodeError, sqlite3.Error) as error:
            payload = {"error": type(error).__name__}
        self.write_receipt(
            started,
            request_hash,
            status,
            count,
            locals().get("tool"),
            locals().get("operation"),
            payload.get("complete") if isinstance(payload, dict) else None,
        )
        self.send_json(code, payload)

    def log_message(self, format: str, *args: Any) -> None:
        return


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--receipts", type=Path, required=True)
    parser.add_argument("--contracts", type=Path, required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    resolved_host = socket.gethostbyname(args.host)
    address = ipaddress.ip_address(resolved_host)
    if not (address.is_loopback or (address.is_private and not address.is_unspecified)):
        raise SystemExit("replay service must bind to loopback or a specific private-network address")
    token = os.environ.get("REPLAY_TOKEN", "")
    if not token:
        raise SystemExit("REPLAY_TOKEN is required")
    Handler.db = args.db
    Handler.receipts = args.receipts
    Handler.token = token
    Handler.snapshot_hash = hashlib.sha256(args.db.read_bytes()).hexdigest()
    Handler.contracts = {
        path.stem: json.loads(path.read_text()) for path in sorted(args.contracts.glob("*.json"))
    }
    ThreadingHTTPServer((resolved_host, args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()

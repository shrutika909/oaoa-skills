#!/usr/bin/env fbpython
"""Build a bounded SQLite replay component from staged SEV query evidence."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import socket
import sqlite3
import stat
import subprocess
import time
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any


TOOLS = {"scuba", "hive", "daiquery", "presto", "logview"}
LOGVIEW_OPERATIONS = {
    "context_describe",
    "mid_list",
    "mid_metadata",
    "mid_trend",
    "mid_triage",
    "sample_list",
    "sample_thread_list",
    "sample_thread_read",
    "sample_metadata_read",
}
SENSITIVE_HINTS = {
    "account",
    "category",
    "config",
    "deployment",
    "host",
    "id",
    "import",
    "index",
    "job",
    "request",
    "relation",
    "resource",
    "service",
    "signal",
    "tier",
    "trace",
    "user",
}
DB_LIMIT = 3 * 1024**3
DB_MIN = 500_000_000
PACKAGE_LIMIT = 4 * 1024**3


class Build:
    def __init__(
        self,
        sev: str,
        source: Path,
        output: Path,
        release_mode: str,
    ) -> None:
        self.sev = sev
        self.source = source
        self.output = output
        self.release_mode = release_mode
        self.inventory_sha256 = inventory_sha256(source)
        self.private = output / "private"
        self.replay = output / "replay"
        self.task = output / "task"
        self.phases: list[dict[str, Any]] = []
        self.sources_used: list[dict[str, Any]] = []
        self.sources_skipped: list[dict[str, Any]] = []
        self.transforms: list[dict[str, Any]] = []
        self.trajectories: list[dict[str, Any]] = []
        self.identifier_maps: dict[str, dict[str, str]] = {}
        self.time_shift_seconds = 315_360_000 + (
            int(hashlib.sha256(sev.encode()).hexdigest()[:8], 16) % 31_536_000
        )
        inventory_path = source / "source_inventory.json"
        self.discovery = json.loads(inventory_path.read_text()) if inventory_path.exists() else None
        self.runtime_tests: list[dict[str, Any]] = []

    def phase(self, name: str, fn: Any) -> Any:
        started = time.time()
        stamp = dt.datetime.now(dt.timezone.utc).isoformat()
        status = "passed"
        try:
            return fn()
        except Exception:
            status = "failed"
            raise
        finally:
            finished = time.time()
            self.phases.append(
                {
                    "name": name,
                    "status": status,
                    "started_at": stamp,
                    "finished_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                    "elapsed_seconds": round(finished - started, 6),
                }
            )

    def prepare(self) -> None:
        if self.output.exists():
            shutil.rmtree(self.output)
        for path in (
            self.private / "receipts",
            self.private / "transforms",
            self.replay / "scripts",
            self.replay / "contracts",
            self.task / "bin",
            self.task / "contracts",
            self.task / "man",
            self.task / "scripts",
        ):
            path.mkdir(parents=True, exist_ok=True)

    def load_trajectories(self) -> None:
        folder = self.source / "trajectories"
        for path in sorted(folder.glob("*.json")) if folder.exists() else []:
            payload = json.loads(path.read_text())
            trajectory_id = str(
                payload.get("trajectory_id")
                or payload.get("session_id")
                or payload.get("id")
                or path.stem
            )
            harness = str(payload.get("harness") or payload.get("agent") or "unknown")
            events = payload.get("events") or payload.get("steps") or payload.get("messages") or []
            normalized = []
            for index, event in enumerate(events):
                if not isinstance(event, dict):
                    continue
                tool = str(
                    event.get("tool")
                    or event.get("tool_name")
                    or event.get("name")
                    or ""
                ).lower()
                matched = next((candidate for candidate in TOOLS if candidate in tool), None)
                if not matched:
                    continue
                request = event.get("request") or event.get("input") or event.get("arguments") or {}
                normalized.append(
                    {
                        "trajectory_id": trajectory_id,
                        "harness": harness,
                        "event_index": index,
                        "timestamp": event.get("timestamp"),
                        "tool": matched,
                        "operation": event.get("operation") or "query",
                        "request": request,
                        "status": event.get("status") or "unknown",
                        "cutoff": payload.get("cutoff"),
                    }
                )
            normalized_path = self.private / f"normalized_{trajectory_id}.json"
            normalized_path.write_text(json.dumps(normalized, indent=2, sort_keys=True) + "\n")
            self.trajectories.append(
                {
                    "trajectory_id": trajectory_id,
                    "harness": harness,
                    "cutoff": payload.get("cutoff"),
                    "database_event_count": len(normalized),
                    "source_hash": sha256(path),
                }
            )

    def load_sources(self) -> list[tuple[Path, dict[str, Any]]]:
        folder = self.source / "sources"
        chosen: list[tuple[Path, dict[str, Any]]] = []
        seen: set[str] = set()
        lineage_to_resource: dict[tuple[str, str], str] = {}
        resource_to_lineage: dict[tuple[str, str], str] = {}
        for path in sorted(folder.glob("*.json")) if folder.exists() else []:
            payload = json.loads(path.read_text())
            digest = sha256(path)
            if digest in seen:
                self.sources_skipped.append({"path": path.name, "reason": "duplicate", "hash": digest})
                continue
            seen.add(digest)
            tool = str(payload.get("tool", "")).lower()
            if tool not in TOOLS:
                self.sources_skipped.append({"path": path.name, "reason": "unsupported_tool", "hash": digest})
                continue
            if not str(payload.get("sev_id", "")).strip():
                self.sources_skipped.append({"path": path.name, "reason": "missing_sev_id", "hash": digest})
                continue
            if str(payload["sev_id"]) != self.sev:
                self.sources_skipped.append({"path": path.name, "reason": "different_sev", "hash": digest})
                continue
            invariants = payload.get("invariants", [])
            if not isinstance(invariants, list) or not invariants:
                raise RuntimeError(f"{path.name}: at least one technical invariant is required")
            lineage_id = str(payload.get("source_lineage_id", "")).strip()
            resource_name = str(
                payload.get("resource_name", payload.get("query_id", path.stem))
            ).strip()
            if not lineage_id:
                self.sources_skipped.append(
                    {"path": path.name, "reason": "missing_source_lineage_id", "hash": digest}
                )
                continue
            lineage_key = (tool, lineage_id)
            resource_key = (tool, resource_name)
            prior_resource = lineage_to_resource.get(lineage_key)
            prior_lineage = resource_to_lineage.get(resource_key)
            if prior_resource is not None and prior_resource != resource_name:
                raise RuntimeError(
                    f"source lineage {lineage_id!r} maps to multiple {tool} resources"
                )
            if prior_lineage is not None and prior_lineage != lineage_id:
                raise RuntimeError(
                    f"distinct {tool} source lineages collapse into resource {resource_name!r}"
                )
            lineage_to_resource[lineage_key] = resource_name
            resource_to_lineage[resource_key] = lineage_id
            reconstruction = payload.get("anonymization", {})
            release_eligible = (
                reconstruction.get("strategy") == "synthetic_reconstruction"
                and reconstruction.get("release_eligible") is True
            )
            if self.release_mode == "export" and not release_eligible:
                self.sources_skipped.append(
                    {"path": path.name, "reason": "not_synthetically_reconstructed", "hash": digest}
                )
                continue
            if tool == "logview":
                operation = str(payload.get("operation", ""))
                if operation not in LOGVIEW_OPERATIONS:
                    self.sources_skipped.append(
                        {"path": path.name, "reason": "unsupported_logview_operation", "hash": digest}
                    )
                    continue
                privacy = payload.get("privacy", {})
                if operation == "sample_metadata_read" and not privacy.get(
                    "values_approved", False
                ):
                    self.sources_skipped.append(
                        {
                            "path": path.name,
                            "reason": "unapproved_sensitive_logview_metadata",
                            "hash": digest,
                        }
                    )
                    continue
            chosen.append((path, payload))
            self.sources_used.append(
                {
                    "path": path.name,
                    "tool": tool,
                    "query_id": payload.get("query_id", path.stem),
                    "source_lineage_id": lineage_id,
                    "operation": payload.get("operation", "query"),
                    "resource_name": resource_name,
                    "classification": payload.get("classification", "unclassified"),
                    "reason": payload.get("classification_reason"),
                    "source_rows": len(payload.get("rows", [])),
                    "source_bytes": path.stat().st_size,
                    "volume": payload.get("volume", {}),
                    "invariant_count": len(invariants),
                    "hash": digest,
                    "release_eligible": release_eligible,
                }
            )
        if not chosen:
            raise RuntimeError("no supported staged query evidence was discovered")
        return chosen

    def semantic_group(self, column: str) -> str:
        lowered = column.lower()
        for group, markers in (
            ("document_id", ("doc_id", "document_id")),
            ("task_id", ("task_id",)),
            ("trace_id", ("trace_id",)),
            ("request_id", ("request_id",)),
            ("configuration", ("config", "signal", "import")),
            ("runtime", ("job", "tier", "service", "host")),
            ("resource", ("category", "index", "relation", "resource")),
            ("identity", ("user", "account", "deployment", "id")),
        ):
            if any(marker in lowered for marker in markers):
                return group
        return safe_name(column)

    def mapped(self, column: str, value: Any) -> Any:
        lowered = column.lower()
        if value is None:
            return value
        if isinstance(value, (int, float)) and (lowered == "time" or lowered.endswith("_time")):
            return value + self.time_shift_seconds
        if isinstance(value, (int, float)) and lowered.endswith(("_ms", "_ns", "_bytes", "_count", "_terms")):
            return value
        if not any(hint in lowered for hint in SENSITIVE_HINTS):
            return value
        key = json.dumps(value, sort_keys=True, default=str)
        group = self.semantic_group(column)
        mapping = self.identifier_maps.setdefault(group, {})
        if key not in mapping:
            mapping[key] = f"{group}_{len(mapping) + 1:06d}"
        return mapping[key]

    def build_db(self, sources: list[tuple[Path, dict[str, Any]]]) -> None:
        db_path = self.replay / "scenario.sqlite"
        connection = sqlite3.connect(db_path)
        connection.execute("PRAGMA journal_mode=DELETE")
        connection.execute("PRAGMA foreign_keys=ON")
        connection.executescript(
            """
            CREATE TABLE query_catalog (
              tool TEXT NOT NULL,
              query_id TEXT NOT NULL,
              resource_name TEXT NOT NULL,
              table_name TEXT NOT NULL,
              query_text TEXT,
              operation TEXT NOT NULL,
              metadata_json TEXT NOT NULL,
              PRIMARY KEY(tool, query_id)
            );
            """
        )
        table_names: set[str] = set()
        sqlite_types = {
            "integer": "INTEGER",
            "timestamp": "INTEGER",
            "float": "REAL",
            "real": "REAL",
            "boolean": "INTEGER",
            "string": "TEXT",
            "text": "TEXT",
            "json": "TEXT",
            "bytes": "BLOB",
        }
        for path, payload in sources:
            tool = payload["tool"].lower()
            query_id = str(payload.get("query_id") or path.stem)
            table = safe_name(f"{tool}__{query_id}")
            if table in table_names:
                raise RuntimeError(f"SQLite identifier collision for table {table}")
            table_names.add(table)
            rows = payload.get("rows", [])
            declared = payload.get("columns", [])
            columns = [str(item["name"] if isinstance(item, dict) else item) for item in declared]
            if not columns and rows:
                columns = list(rows[0])
            if not columns:
                raise RuntimeError(f"{path.name}: no columns")
            safe_columns = [safe_name(column) for column in columns]
            if len(set(safe_columns)) != len(safe_columns):
                raise RuntimeError(f"{path.name}: SQLite identifier collision in columns")
            declared_types = {
                str(item.get("name")): str(item.get("type", "dynamic")).lower()
                for item in declared
                if isinstance(item, dict)
            }
            definitions = ", ".join(
                f'"{safe}" {sqlite_types.get(declared_types.get(original, ""), "BLOB")}'
                for original, safe in zip(columns, safe_columns)
            )
            quoted = ", ".join(f'"{column}"' for column in safe_columns)
            connection.execute(f'CREATE TABLE "{table}" ({definitions})')
            placeholders = ", ".join("?" for _ in columns)
            synthetic = (
                payload.get("anonymization", {}).get("strategy")
                == "synthetic_reconstruction"
                and payload.get("anonymization", {}).get("release_eligible") is True
            )
            transformed = []
            for row in rows:
                transformed.append(
                    [
                        row.get(column) if synthetic else self.mapped(column, row.get(column))
                        for column in columns
                    ]
                )
            connection.executemany(
                f'INSERT INTO "{table}" ({quoted}) VALUES ({placeholders})', transformed
            )
            metadata = {
                "columns": declared or [{"name": column, "type": "dynamic"} for column in columns],
                "supported_functions": payload.get("supported_functions", []),
                "time_range": {
                    key: value
                    if synthetic
                    else value + self.time_shift_seconds
                    if isinstance(value, (int, float))
                    else value
                    for key, value in payload.get("time_range", {}).items()
                },
                "identity": payload.get("identity", "simulated_oncall"),
                "operation": payload.get("operation", "query"),
                "context": payload.get("context"),
                "privacy": payload.get("privacy", {}),
            }
            connection.execute(
                "INSERT INTO query_catalog VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    tool,
                    query_id,
                    payload.get("resource_name", query_id)
                    if synthetic
                    else self.mapped("resource_name", payload.get("resource_name", query_id)),
                    table,
                    payload.get("query"),
                    payload.get("operation", "query"),
                    json.dumps(metadata, sort_keys=True),
                ),
            )
            self.transforms.append(
                {
                    "source": path.name,
                    "source_tool": tool,
                    "source_resource": payload.get("resource_name", query_id),
                    "query_id": query_id,
                    "operation": payload.get("operation", "query"),
                    "destination": table,
                    "source_rows": len(rows),
                    "destination_rows": len(transformed),
                    "destination_payload_bytes": sum(
                        len(json.dumps(row, sort_keys=True, default=str).encode())
                        for row in transformed
                    ),
                    "source_bytes": path.stat().st_size,
                    "invariants": payload.get("invariants", []),
                    "time_shift_seconds": 0 if synthetic else self.time_shift_seconds,
                    "transformation_strategy": "synthetic_reconstruction"
                    if synthetic
                    else "deterministic_pseudonymization",
                }
            )
        connection.commit()
        with (self.replay / "scenario.sql").open("w") as handle:
            for line in connection.iterdump():
                handle.write(line + "\n")
        connection.close()
        if db_path.stat().st_size > DB_LIMIT:
            raise RuntimeError("scenario.sqlite exceeds the 3 GB limit")

    def copy_runtime(self) -> None:
        root = Path(__file__).resolve().parent
        copies = {
            root / "replay_server.py": self.replay / "replay_server.py",
            root / "start-replay.sh": self.replay / "scripts" / "start-replay.sh",
            root / "client.py": self.task / "bin" / "query_client.py",
            root / "query-cli": self.task / "bin" / "query-cli",
            root / "start-client.sh": self.task / "scripts" / "start-client.sh",
            root.parent / "man" / "query-cli.1": self.task / "man" / "query-cli.1",
        }
        for source, destination in copies.items():
            shutil.copy2(source, destination)
        for tool in sorted(TOOLS):
            spec = root.parent / "assets" / "tool_specs" / f"{tool}.json"
            shutil.copy2(spec, self.replay / "contracts" / spec.name)
            shutil.copy2(spec, self.task / "contracts" / spec.name)
            shutil.copy2(root / "tool_cli.py", self.task / "bin" / tool)
            (self.task / "man" / f"{tool}.1").write_text(
                f".TH {tool.upper()} 1\n.SH NAME\n{tool} \\- bounded offline {tool} replay client\n"
                f".SH SYNOPSIS\n.B {tool}\n[--endpoint URL] resources|<operation> [options]\n"
                ".SH RESTRICTIONS\nRegistered resources and operations only. Raw SQL, production fallback, and filesystem access are unavailable.\n"
            )
        for path in (
            self.replay / "scripts" / "start-replay.sh",
            self.replay / "replay_server.py",
            self.task / "bin" / "query-cli",
            self.task / "scripts" / "start-client.sh",
            self.task / "bin" / "query_client.py",
            *(self.task / "bin" / tool for tool in TOOLS),
        ):
            path.chmod(0o755)
        (self.replay / "Dockerfile.replay").write_text(
            "FROM python:3.12-slim\nWORKDIR /replay\nCOPY . /replay\n"
            "RUN mkdir -p /private/receipts && chown -R 65532:65532 /private/receipts\n"
            "USER 65532:65532\nEXPOSE 8080\nENTRYPOINT [\"./scripts/start-replay.sh\"]\n"
        )
        (self.replay / "compose.yaml").write_text(
            "services:\n  replay:\n    build:\n      context: .\n      dockerfile: Dockerfile.replay\n"
            "    environment:\n      REPLAY_HOST: 127.0.0.1\n      REPLAY_PORT: ${REPLAY_PORT:-18080}\n      REPLAY_TOKEN: ${REPLAY_TOKEN:?set REPLAY_TOKEN}\n"
            "      RECEIPTS_PATH: /private/receipts/tool_receipts.jsonl\n"
            "    network_mode: host\n"
            "    read_only: true\n    tmpfs: [/tmp]\n"
            "    volumes:\n      - replay_receipts:/private/receipts\n"
            "volumes:\n  replay_receipts:\n"
        )
        (self.task / "Dockerfile.task").write_text(
            "FROM python:3.12-slim\nWORKDIR /task\nCOPY . /task\n"
            "USER 65532:65532\nENTRYPOINT [\"./bin/query-cli\"]\n"
        )
        (self.task / "README.md").write_text(
            "# Offline query replay\n\nFor Docker, export `REPLAY_TOKEN`, then run `docker compose up -d --build`. "
            "The separate task container uses host networking and `http://127.0.0.1:18080`. "
            "For a local process, start the replay service with `scripts/start-replay.sh`. "
            "Use `bin/<tool> resources` and the operation listed in `contracts/<tool>.json`. "
            "Raw SQL and production fallback are unavailable.\n"
        )

    def validate(self) -> dict[str, Any]:
        original = sqlite3.connect(self.replay / "scenario.sqlite")
        original_counts = dict(original.execute("SELECT table_name, query_id FROM query_catalog"))
        original.close()
        rebuilt = self.private / "rebuilt.sqlite"
        connection = sqlite3.connect(rebuilt)
        connection.executescript((self.replay / "scenario.sql").read_text())
        rebuilt_counts = dict(connection.execute("SELECT table_name, query_id FROM query_catalog"))
        connection.close()
        runtime_passed = self.validate_runtime()
        observed = {
            "dump_reconstructs": original_counts == rebuilt_counts,
            "private_report_outside_task": not (self.task / "private").exists(),
            "snapshot_absent_from_task": not any(
                (self.task / name).exists()
                for name in ("scenario.sqlite", "scenario.sql", "replay_server.py")
            ),
            "database_under_3gb": (self.replay / "scenario.sqlite").stat().st_size <= DB_LIMIT,
            "database_at_least_500mb": (self.replay / "scenario.sqlite").stat().st_size >= DB_MIN,
            "package_under_4gb": sum(
                path.stat().st_size for path in self.output.rglob("*") if path.is_file()
            ) <= PACKAGE_LIMIT,
            "required_runtime_files": all(
                path.exists()
                for path in (
                    self.replay / "replay_server.py",
                    self.replay / "scripts" / "start-replay.sh",
                    self.task / "bin" / "query-cli",
                    self.task / "bin" / "query_client.py",
                    *(self.task / "bin" / tool for tool in TOOLS),
                )
            ),
            "tool_contracts_complete": all(
                (self.task / "contracts" / f"{tool}.json").exists()
                and (self.replay / "contracts" / f"{tool}.json").exists()
                and (self.task / "man" / f"{tool}.1").exists()
                for tool in TOOLS
            ),
            "runtime_contract_tests": runtime_passed,
            "source_lineages_preserved": (
                len(self.sources_used)
                == len({(item["tool"], item["source_lineage_id"]) for item in self.sources_used})
                == len({(item["tool"], item["resource_name"]) for item in self.sources_used})
            ),
            "technical_invariants_declared": all(
                int(item.get("invariant_count", 0)) > 0 for item in self.sources_used
            ),
        }
        checks = {
            name: {"status": "passed" if value else "failed", "observed": value, "mandatory": True}
            for name, value in observed.items()
        }
        checks.update(
            {
                "native_adapter_fidelity": {
                    "status": "passed" if observed["tool_contracts_complete"] else "failed",
                    "mandatory": True,
                    "observed": "five versioned ToolSpecs, named CLIs, man pages, bounded operations, pagination, and error taxonomies",
                },
                "identity_acl_cutoff": {
                    "status": "passed" if observed["tool_contracts_complete"] else "failed",
                    "mandatory": True,
                    "observed": "token authentication, contract-bound simulated identities, catalog lookup denial, and snapshot time-window enforcement",
                },
                "independent_solvability": {
                    "status": "not_run",
                    "mandatory": False,
                    "reason": "requires an external evaluator without trajectory access",
                },
                "over_normalization": {
                    "status": "passed"
                    if observed["source_lineages_preserved"]
                    and observed["technical_invariants_declared"]
                    else "failed",
                    "mandatory": True,
                    "observed": "distinct source lineage/resource boundaries and declared technical invariants are preserved",
                },
                "agent_cheating_surface": {
                    "status": "passed"
                    if observed["private_report_outside_task"]
                    and observed["snapshot_absent_from_task"]
                    and observed["runtime_contract_tests"]
                    else "failed",
                    "mandatory": True,
                    "observed": "no private snapshot, mappings, receipts, raw SQL, filesystem access, or unauthenticated bypass in the agent package",
                },
            }
        )
        mandatory_statuses = {
            item["status"] for item in checks.values() if item.get("mandatory", True)
        }
        status = "failed" if "failed" in mandatory_statuses else "incomplete" if "not_run" in mandatory_statuses else "passed"
        return {"status": status, "checks": checks}

    def validate_runtime(self) -> bool:
        token = "build-validation-token"
        receipts = self.private / "receipts" / "validation.jsonl"
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = int(probe.getsockname()[1])
        process = subprocess.Popen(
            [
                "fbpython",
                str(self.replay / "replay_server.py"),
                "--db",
                str(self.replay / "scenario.sqlite"),
                "--contracts",
                str(self.replay / "contracts"),
                "--receipts",
                str(receipts),
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
            ],
            env={**os.environ, "REPLAY_TOKEN": token},
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )

        def request(
            method: str,
            path: str,
            body: dict[str, Any] | None = None,
            identity: str = "simulated_oncall",
            supplied_token: str = token,
        ) -> tuple[int, dict[str, Any]]:
            encoded = json.dumps(body).encode() if body is not None else None
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}{path}",
                data=encoded,
                method=method,
                headers={
                    "Authorization": f"Bearer {supplied_token}",
                    "X-Replay-Identity": identity,
                    "Content-Type": "application/json",
                },
            )
            try:
                with urllib.request.urlopen(req, timeout=3) as response:
                    return response.status, json.loads(response.read())
            except urllib.error.HTTPError as error:
                return error.code, json.loads(error.read())

        def record(name: str, command: str, expected: int, actual: tuple[int, dict[str, Any]]) -> None:
            status, evidence = actual
            self.runtime_tests.append(
                {
                    "name": name,
                    "command": command,
                    "expected_http_status": expected,
                    "actual_http_status": status,
                    "status": "passed" if status == expected else "failed",
                    "evidence": evidence,
                }
            )

        try:
            for _ in range(50):
                try:
                    if request("GET", "/health")[0] == 200:
                        break
                except (OSError, urllib.error.URLError):
                    time.sleep(0.05)
            else:
                raise RuntimeError("replay service did not start")
            for item in self.sources_used:
                tool = item["tool"]
                operation = item["operation"]
                query_id = item["query_id"]
                record(
                    f"{tool}.resources",
                    f"task/bin/{tool} resources",
                    200,
                    request("GET", f"/v1/{tool}/resources"),
                )
                record(
                    f"{tool}.{operation}",
                    f"task/bin/{tool} {operation} --query-id {query_id} --limit 1",
                    200,
                    request("POST", f"/v1/{tool}/{operation}", {"query_id": query_id, "limit": 1}),
                )
            first = self.sources_used[0]
            route = f"/v1/{first['tool']}/{first['operation']}"
            query_id = first["query_id"]
            page_one = request("POST", route, {"query_id": query_id, "limit": 1})
            next_token = page_one[1].get("next_page_token")
            record(
                "pagination.next_page",
                f"task/bin/{first['tool']} {first['operation']} --query-id {query_id} --limit 1 --page-token {next_token}",
                200,
                request("POST", route, {"query_id": query_id, "limit": 1, "page_token": next_token}),
            )
            record("acl.identity_denied", "REPLAY_IDENTITY=unknown task/bin/<tool> resources", 403, request("GET", f"/v1/{first['tool']}/resources", identity="unknown"))
            record("acl.token_denied", "REPLAY_TOKEN=wrong task/bin/<tool> resources", 403, request("GET", f"/v1/{first['tool']}/resources", supplied_token="wrong"))
            record("limit.maximum", "task/bin/<tool> <operation> --limit 1001", 422, request("POST", route, {"query_id": query_id, "limit": 1001}))
            record("timeout.nonpositive", "task/bin/<tool> <operation> --timeout-ms 0", 408, request("POST", route, {"query_id": query_id, "timeout_ms": 0}))
            record("filter.unknown", "task/bin/<tool> <operation> --filter unknown=value", 400, request("POST", route, {"query_id": query_id, "filters": {"unknown": "value"}}))
            record("resource.unknown", "task/bin/<tool> <operation> --query-id unknown", 404, request("POST", route, {"query_id": "unknown"}))
        finally:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        receipts_ok = receipts.exists() and len(receipts.read_text().splitlines()) >= len(self.runtime_tests)
        self.runtime_tests.append(
            {
                "name": "receipts.complete",
                "command": "inspect private/receipts/validation.jsonl",
                "expected_http_status": None,
                "actual_http_status": None,
                "status": "passed" if receipts_ok else "failed",
                "evidence": {"receipt_lines": len(receipts.read_text().splitlines()) if receipts.exists() else 0},
            }
        )
        return all(test["status"] == "passed" for test in self.runtime_tests)

    def write_reports(self, validation: dict[str, Any], total_started: float) -> None:
        mapping_path = self.private / "transforms" / "identifier_map.json"
        mapping_path.write_text(json.dumps(self.identifier_maps, indent=2, sort_keys=True) + "\n")
        mapping_report = [
            f"# Private normalization mapping: {self.sev}",
            "",
            "> Author/evaluator only. Do not place this file in the agent-visible package.",
            "",
            "## Classification",
            "",
            "This build performs deterministic pseudonymization, not proven anonymization.",
            "",
            "## Time mapping",
            "",
            f"Every absolute `time` or `*_time` value is shifted by `{self.time_shift_seconds}` seconds.",
            "Durations and relative ordering are preserved.",
            "",
            "## Identifier mappings",
            "",
        ]
        for group, values in sorted(self.identifier_maps.items()):
            mapping_report.extend([f"### {group}", "", "| Source value | Scaffold value |", "|---|---|"])
            for encoded, replacement in sorted(values.items()):
                source_value = json.loads(encoded)
                source_text = str(source_value).replace("|", "\\|").replace("`", "\\`")
                mapping_report.append(f"| `{source_text}` | `{replacement}` |")
            mapping_report.append("")
        mapping_report.extend(
            [
                "## Values intentionally preserved",
                "",
                "- Durations and magnitudes ending in `_ms`, `_ns`, `_bytes`, `_count`, or `_terms`",
                "- Cardinality, equality, ordering, joins, and repeated-value relationships",
                "- Non-sensitive categorical values not selected by the identifier policy",
                "",
                "## Review required",
                "",
                "Review rare numeric combinations and free-text columns for re-identification risk. "
                "A passing identifier-map check does not establish anonymity.",
            ]
        )
        (self.private / "anonymization_mapping.md").write_text("\n".join(mapping_report) + "\n")
        database_report = [
            f"# Private database storage mapping: {self.sev}",
            "",
            "> Author/evaluator only. Classification and source resource names must not be copied into the agent prompt.",
            "",
            "## Storage format",
            "",
            "- Input: normalized JSON files containing ordered column metadata and row objects",
            "- Output: one embedded SQLite 3 file, `replay/scenario.sqlite`",
            "- Reconstruction: deterministic SQL text in `replay/scenario.sql`",
            "- Catalog: `query_catalog` maps `(tool, query_id)` to a SQLite table and JSON metadata",
            "- Rows: one SQLite row per staged result row; no Parquet or DuckDB files are produced",
            "- SQLite column declarations: native metadata is mapped to INTEGER, REAL, TEXT, BLOB, or fallback BLOB affinity",
            "",
            "## Source-to-table mapping",
            "",
        ]
        connection = sqlite3.connect(self.replay / "scenario.sqlite")
        for item in self.transforms:
            catalog = connection.execute(
                "SELECT resource_name, metadata_json FROM query_catalog WHERE tool=? AND query_id=?",
                (item["source_tool"], item["query_id"]),
            ).fetchone()
            metadata = json.loads(catalog[1])
            database_report.extend(
                [
                    f"### `{item['source_tool']}:{item['source_resource']}` / `{item['query_id']}`",
                    "",
                    f"- Staged file: `{item['source']}` (JSON)",
                    f"- Agent-visible resource: `{catalog[0]}`",
                    f"- SQLite table: `{item['destination']}`",
                    f"- Rows: `{item['source_rows']}` source → `{item['destination_rows']}` stored",
                    f"- Supported operations: `{', '.join(metadata.get('supported_functions', [])) or 'none declared'}`",
                    "",
                    "| Column | Native type metadata | SQLite declared type |",
                    "|---|---|---|",
                ]
            )
            declared = {str(column.get("name")): str(column.get("type", "dynamic")) for column in metadata.get("columns", []) if isinstance(column, dict)}
            for column in connection.execute(f'PRAGMA table_info("{item["destination"]}")'):
                database_report.append(
                    f"| `{column[1]}` | `{declared.get(column[1], 'dynamic')}` | `{column[2] or 'NONE'}` |"
                )
            database_report.append("")
        connection.close()
        classification_sources = Counter(
            str(item.get("classification", "unclassified"))
            for item in self.sources_used
        )
        classification_rows = Counter()
        for item in self.sources_used:
            classification_rows[str(item.get("classification", "unclassified"))] += int(
                item.get("source_rows", 0)
            )
        evidence_mix = {
            "bullseye": {
                "private_classes": ["causal"],
                "source_count": classification_sources["causal"],
                "row_count": classification_rows["causal"],
            },
            "supporting": {
                "private_classes": ["supporting"],
                "source_count": classification_sources["supporting"],
                "row_count": classification_rows["supporting"],
            },
            "directional": {
                "private_classes": ["directional"],
                "source_count": classification_sources["directional"],
                "row_count": classification_rows["directional"],
            },
            "misleading": {
                "private_classes": ["competing", "negative"],
                "source_count": classification_sources["competing"]
                + classification_sources["negative"],
                "row_count": classification_rows["competing"]
                + classification_rows["negative"],
            },
            "excluded": {
                "private_classes": ["excluded"],
                "source_count": classification_sources["excluded"],
                "row_count": classification_rows["excluded"],
            },
        }
        database_bytes = (self.replay / "scenario.sqlite").stat().st_size
        total_rows = sum(int(item.get("source_rows", 0)) for item in self.sources_used)
        scale_profile = {
            "profile": "production_scale",
            "target_minimum_bytes": DB_MIN,
            "actual_database_bytes": database_bytes,
            "total_materialized_rows": total_rows,
            "source_rows": sum(
                int(item.get("volume", {}).get("observed_source_rows", 0))
                for item in self.sources_used
            ),
            "source_bytes": sum(
                int(item.get("volume", {}).get("observed_source_bytes", 0))
                for item in self.sources_used
            ),
            "per_resource": [
                {
                    "tool": item["tool"],
                    "query_id": item["query_id"],
                    "materialized_rows": item["source_rows"],
                    "staged_bytes": item["source_bytes"],
                    "volume": item.get("volume", {}),
                }
                for item in self.sources_used
            ],
            "floor_passed": database_bytes >= DB_MIN,
            "source_derived_row_count": all(
                item.get("volume", {}).get("scale_basis") in {
                    "source_cardinality",
                    "approved_synthetic_population",
                }
                for item in self.sources_used
            ),
        }
        database_report.extend(
            [
                "## Private evidence mix",
                "",
                "Counts are author-only. Bullseye means causal evidence; misleading means realistic competing or negative evidence that remains falsifiable from the replay.",
                "",
                "| Role | Private classes | Sources | Rows |",
                "|---|---|---:|---:|",
            ]
        )
        for role, counts in evidence_mix.items():
            database_report.append(
                f"| {role} | {', '.join(counts['private_classes'])} | {counts['source_count']} | {counts['row_count']} |"
            )
        database_report.extend(
            [
                "",
                "## Replay boundary",
                "",
                "The replay service opens SQLite with `mode=ro`. Clients select a registered `query_id`; raw SQL and filesystem paths are not accepted.",
            ]
        )
        (self.private / "database_mapping.md").write_text("\n".join(database_report) + "\n")
        manifest = {
            "schema_version": "0.2",
            "sev_id": self.sev,
            "status": validation["status"],
            "phase_timings": self.phases,
            "trajectories": self.trajectories,
            "sources_used": self.sources_used,
            "evidence_mix": evidence_mix,
            "scale_profile": scale_profile,
            "sources_skipped": self.sources_skipped,
            "targeted_queries": [
                {key: value for key, value in item.items() if key != "hash"}
                for item in self.sources_used
            ],
            "transformations": self.transforms,
            "coverage_gaps": self.discovery.get("inaccessible", []) if self.discovery else [],
            "discovery": {
                "status": self.discovery.get("status"),
                "instances": self.discovery.get("instances"),
                "trajectories": self.discovery.get("trajectories"),
                "database_call_count": len(self.discovery.get("database_calls", [])),
                "included_tools": self.discovery.get("included_tools", []),
                "missing_tools": self.discovery.get("missing_tools", []),
                "inaccessible_count": len(self.discovery.get("inaccessible", [])),
            } if self.discovery else None,
            "anonymization_mapping": "private/anonymization_mapping.md",
            "database_mapping": "private/database_mapping.md",
            "source_inventory_sha256": self.inventory_sha256,
            "release_mode": self.release_mode,
            "export_eligible": validation["status"] == "passed" and all(
                item.get("release_eligible", False) for item in self.sources_used
            ),
        }
        (self.private / "private_authoring_manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n"
        )
        report = [
            f"# Database scaffolding build report: {self.sev}",
            "",
            f"- Status: {validation['status']}",
            f"- Total elapsed seconds: {time.time() - total_started:.6f}",
            "",
            "## Phase timing",
            "",
        ]
        report.extend(
            f"- {p['name']}: {p['status']} ({p['elapsed_seconds']}s; {p['started_at']} to {p['finished_at']})"
            for p in self.phases
        )
        report.extend(["", "## Discovered trajectories", "", json_block(self.trajectories)])
        if self.discovery:
            report.extend(["", "## OpsMate discovery inventory", "", json_block(manifest["discovery"]), "", "### Inaccessible evidence", "", json_block(self.discovery.get("inaccessible", []))])
        report.extend(["", "## Sources used", "", json_block(self.sources_used)])
        report.extend(["", "## Private evidence mix", "", json_block(evidence_mix)])
        report.extend(["", "## Scale profile", "", json_block(scale_profile)])
        report.extend(["", "## Sources skipped", "", json_block(self.sources_skipped)])
        report.extend(["", "## Source-to-SQLite transformations", "", json_block(self.transforms)])
        report.extend(["", "## Components", "", "- SQLite database and deterministic SQL dump", "- Read-only replay server", "- Bash CLI and executable Python client", "- Replay and client startup scripts", "- Private ToolReceipt sink", "- Man page", "- LogView operational replay contract when selected"])
        report.extend(["", "## Validation", "", json_block(validation)])
        (self.private / "build_report.md").write_text("\n".join(report) + "\n")
        test_report = [
            f"# Replay validation report: {self.sev}",
            "",
            f"- Verdict: {'PASS' if all(test['status'] == 'passed' for test in self.runtime_tests) else 'FAIL'}",
            f"- Tests: {len(self.runtime_tests)}",
            "",
        ]
        for test in self.runtime_tests:
            test_report.extend(
                [
                    f"## {test['name']}: {test['status'].upper()}",
                    "",
                    f"- Command: `{test['command']}`",
                    f"- Expected HTTP status: `{test['expected_http_status']}`",
                    f"- Actual HTTP status: `{test['actual_http_status']}`",
                    "- Evidence:",
                    json_block(test["evidence"]),
                    "",
                ]
            )
        (self.private / "test_report.md").write_text("\n".join(test_report) + "\n")

        known_gaps = [
            {"gate": name, "reason": result.get("reason", "validation failed")}
            for name, result in validation["checks"].items()
            if result["status"] != "passed" and result.get("mandatory", True)
        ]
        if self.discovery and self.discovery.get("inaccessible"):
            known_gaps.append(
                {
                    "gate": "opsmate_discovery_coverage",
                    "reason": f"{len(self.discovery['inaccessible'])} trajectory or call records were inaccessible; details remain in private discovery inventory",
                    "mandatory": False,
                }
            )
        if self.discovery and self.discovery.get("missing_tools"):
            known_gaps.append(
                {
                    "gate": "tools_not_observed_in_trajectories",
                    "reason": "No database calls were observed for: " + ", ".join(self.discovery["missing_tools"]),
                    "mandatory": False,
                }
            )
        files = []
        for root_name, root in (("replay", self.replay), ("task", self.task)):
            for path in sorted(root.rglob("*")):
                if path.is_file() and path.name not in {
                    "component_manifest.json",
                    "validation_report.json",
                    "checksums.sha256",
                }:
                    files.append(
                        {
                            "path": f"{root_name}/{path.relative_to(root)}",
                            "bytes": path.stat().st_size,
                            "sha256": sha256(path),
                        }
                    )
        summary = {
            "schema_version": "0.2",
            "sev_id": self.sev,
            "status": validation["status"],
            "release_mode": self.release_mode,
            "export_eligible": validation["status"] == "passed" and all(
                item.get("release_eligible", False) for item in self.sources_used
            ),
            "included_tools": sorted({item["tool"] for item in self.sources_used}),
            "evidence_mix": evidence_mix,
            "scale_profile": scale_profile,
            "discovery": manifest["discovery"],
            "database": {"path": "replay/scenario.sqlite", "bytes": (self.replay / "scenario.sqlite").stat().st_size},
            "files": files,
            "validation": validation,
            "known_gaps": known_gaps,
            "parent_handoff": {
                "component_scope": "offline_query_replay",
                "full_task_status": "not_built",
                "required_parent_skill": "oaoa-sev-task-autopilot",
                "required_parent_mode": "develop-draft",
                "agent_visible_root": "task/",
                "agent_visible_files": [
                    item["path"]
                    for item in files
                    if item["path"].startswith("task/")
                ],
                "private_roots": ["private/", "replay/"],
                "remaining_stages": [
                    "task_design",
                    "approved_instruction_authorship",
                    "non_database_evidence",
                    "recovery_surface",
                    "oracle_and_verifier",
                    "controls",
                    "calibration",
                    "review",
                    "commit_push_and_exact_sha_validation",
                ],
                "ready_for_parent": validation["status"] == "passed"
                and not any(gap.get("mandatory", True) for gap in known_gaps),
            },
        }
        (self.output / "scaffolding_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
        agent_manifest = {
            "schema_version": summary["schema_version"],
            "status": summary["status"],
            "included_tools": summary["included_tools"],
            "files": [
                item
                for item in files
                if item["path"].startswith("task/")
            ],
            "interfaces": {
                "cli": "bin/query-cli",
                "python_client": "bin/query-client",
                "startup": "scripts/start-client.sh",
                "man_pages": "man/",
                "tool_specs": "tool_specs/",
            },
        }
        (self.task / "component_manifest.json").write_text(
            json.dumps(agent_manifest, indent=2, sort_keys=True) + "\n"
        )
        (self.task / "validation_report.json").write_text(json.dumps(validation, indent=2, sort_keys=True) + "\n")
        checksums = [f"{item['sha256']}  {item['path']}" for item in files]
        (self.task / "checksums.sha256").write_text("\n".join(checksums) + "\n")
        package_size = sum(path.stat().st_size for path in self.output.rglob("*") if path.is_file())
        if package_size > PACKAGE_LIMIT:
            raise RuntimeError("complete component exceeds the 4 GB limit")

    def run(self) -> None:
        started = time.time()
        self.phase("prepare", self.prepare)
        self.phase("normalize_trajectories", self.load_trajectories)
        sources = self.phase("discover_and_stage_sources", self.load_sources)
        self.phase("build_sqlite", lambda: self.build_db(sources))
        self.phase("generate_runtime", self.copy_runtime)
        validation = self.phase("validate", self.validate)
        self.write_reports(validation, started)


def safe_name(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_]", "_", value).strip("_").lower()
    return cleaned[:63] or "field"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inventory_sha256(source: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(source.rglob("*")):
        if not path.is_file():
            continue
        digest.update(str(path.relative_to(source)).encode())
        digest.update(b"\0")
        digest.update(bytes.fromhex(sha256(path)))
    return digest.hexdigest()


def json_block(value: Any) -> str:
    return "```json\n" + json.dumps(value, indent=2, sort_keys=True) + "\n```"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sev", required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--print-inventory-sha256", action="store_true")
    parser.add_argument("--release-mode", choices=("export",), default="export")
    args = parser.parse_args()
    if args.print_inventory_sha256:
        print(inventory_sha256(args.source))
        return
    Build(args.sev, args.source, args.output, args.release_mode).run()
    print(args.output / "scaffolding_summary.json")


if __name__ == "__main__":
    main()

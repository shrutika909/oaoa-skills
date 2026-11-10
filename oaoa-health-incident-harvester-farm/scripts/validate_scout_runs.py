#!/usr/bin/env python3
"""Validate two independent Health Incident evidence-scout run receipts."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import sys


ROLES = {"directional", "misleading"}
SHA256 = re.compile(r"[0-9a-f]{64}")


class ContractError(ValueError):
    pass


def load(path: pathlib.Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ContractError(f"cannot read JSON object: {path}") from error
    if not isinstance(value, dict):
        raise ContractError(f"JSON document must be an object: {path}")
    return value


def file_sha(path: pathlib.Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as error:
        raise ContractError(f"cannot read scout output: {path}") from error


def validate(build: dict, document: dict) -> dict:
    if build.get("status") != "PASS" or set(build.get("scout_roles") or []) != ROLES:
        raise ContractError("world build receipt must PASS with exactly two scout roles")
    if document.get("schema") != "oaoa.incident-scout-runs.v1":
        raise ContractError("invalid scout-runs schema")
    world_sha = build.get("incident_world_sha256")
    if not isinstance(world_sha, str) or not SHA256.fullmatch(world_sha):
        raise ContractError("world build receipt has no valid content binding")
    if document.get("incident_world_sha256") != world_sha:
        raise ContractError("scout runs are bound to a different incident world")
    runs = document.get("runs")
    if not isinstance(runs, list) or len(runs) != 2:
        raise ContractError("exactly two scout runs are required")
    by_role, sessions = {}, set()
    input_hashes = build.get("scout_input_sha256") or {}
    for run in runs:
        if not isinstance(run, dict):
            raise ContractError("scout run must be an object")
        role = run.get("role")
        if role not in ROLES or role in by_role:
            raise ContractError("scout roles must be unique and complete")
        if run.get("status") != "PASS":
            raise ContractError(f"{role} scout did not PASS")
        session = run.get("session_id")
        if not isinstance(session, str) or not session.strip() or session in sessions:
            raise ContractError("scout sessions must be present and independent")
        sessions.add(session)
        for key in ("provider", "model"):
            if not isinstance(run.get(key), str) or not run[key].strip():
                raise ContractError(f"{role} scout is missing {key}")
        if run.get("input_sha256") != input_hashes.get(role):
            raise ContractError(f"{role} scout input binding is invalid")
        expected = run.get("output_sha256")
        if not isinstance(expected, str) or not SHA256.fullmatch(expected):
            raise ContractError(f"{role} scout output binding is invalid")
        path = pathlib.Path(str(run.get("output_path") or ""))
        if file_sha(path) != expected:
            raise ContractError(f"{role} scout output hash mismatch")
        by_role[role] = run
    if set(by_role) != ROLES:
        raise ContractError("both directional and misleading scouts are required")
    return {
        "schema": "oaoa.incident-scout-validation-receipt.v1",
        "status": "PASS",
        "incident_world_sha256": world_sha,
        "sessions": sorted(sessions),
        "output_sha256": {role: by_role[role]["output_sha256"] for role in sorted(ROLES)},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build-receipt", required=True, type=pathlib.Path)
    parser.add_argument("--runs", required=True, type=pathlib.Path)
    args = parser.parse_args()
    try:
        receipt = validate(load(args.build_receipt), load(args.runs))
    except ContractError as error:
        print(f"BLOCKED: {error}", file=sys.stderr)
        return 1
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

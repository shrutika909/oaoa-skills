#!/usr/bin/env python3
"""Evaluate Health Incident registry and accessible dedupe evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "oaoa.health-incident-registry-gate.v1"
REQUIRED_DEDUPE_CHECKS = (
    "repository",
    "cards",
    "retired_tasks",
    "rejected_tasks",
    "semantic_dedupe",
)


class GateError(ValueError):
    pass


def require_sha256(value: object, field: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise GateError(f"{field} must be a lowercase SHA-256")
    if value.lower() != value or any(character not in "0123456789abcdef" for character in value):
        raise GateError(f"{field} must be a lowercase SHA-256")
    return value


def decision(status: str, *, private: bool, local: bool, external: bool) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "private_research_allowed": private,
        "local_prototype_allowed": local,
        "external_intake_allowed": external,
        "publication_allowed": external,
        "submission_allowed": False,
    }


def evaluate(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise GateError(f"schema_version must be {SCHEMA_VERSION}")
    require_sha256(
        payload.get("stable_source_key_sha256"), "stable_source_key_sha256"
    )

    checks = payload.get("dedupe_checks")
    if not isinstance(checks, dict):
        raise GateError("dedupe_checks must be an object")
    for name in REQUIRED_DEDUPE_CHECKS:
        if name not in checks:
            raise GateError(f"dedupe_checks.{name} is required")
        if checks[name] not in ("clear", "conflict"):
            raise GateError(f"dedupe_checks.{name} must be clear or conflict")
    if any(checks[name] == "conflict" for name in REQUIRED_DEDUPE_CHECKS):
        return decision(
            "KNOWN_DUPLICATE_BLOCKED", private=False, local=False, external=False
        )

    registry = payload.get("registry")
    if not isinstance(registry, dict):
        raise GateError("registry must be an object")
    registry_status = registry.get("status")
    if registry_status == "claimed":
        require_sha256(
            registry.get("fenced_claim_receipt_sha256"),
            "registry.fenced_claim_receipt_sha256",
        )
        return decision(
            "FENCED_CLAIM_CONFIRMED", private=True, local=True, external=True
        )
    if registry_status == "unavailable":
        require_sha256(
            registry.get("attempt_receipt_sha256"),
            "registry.attempt_receipt_sha256",
        )
        return decision(
            "REGISTRY_UNAVAILABLE_CONTINUING_LOCAL",
            private=True,
            local=True,
            external=False,
        )
    if registry_status == "conflict":
        return decision(
            "REGISTRY_CONFLICT_BLOCKED", private=False, local=False, external=False
        )
    raise GateError("registry.status must be claimed, unavailable, or conflict")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise GateError("input must be a JSON object")
        result = evaluate(payload)
    except (OSError, json.JSONDecodeError, GateError) as error:
        print(f"REGISTRY_GATE_ERROR: {error}", file=sys.stderr)
        return 1
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

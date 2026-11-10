#!/usr/bin/env python3
"""Build a label-free fictional Health Incident world and two scout inputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import sys


WORLD_SCHEMA = "oaoa.agent-incident-world.v1"
SPEC_SCHEMA = "oaoa.health-incident-abstract-spec.v1"
SCOUT_ROLES = ("directional", "misleading")
SHA256 = re.compile(r"[0-9a-f]{64}")
NAME = re.compile(r"[a-z][a-z0-9_-]{1,79}")
PRIVATE = re.compile(
    r"(?ix)(?:"
    r"\b[STDP]\d{5,}\b|"
    r"https?://\S*(?:internalfb|internalmeta|tfbnw|facebook)\S*|"
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b|"
    r"\b(?:health[ _-]?incident|logview|opsmate|ace|trajectory|"
    r"experiment[ _-]?id|session[ _-]?id|prompt[ _-]?id|grader[ _-]?id|"
    r"run[ _-]?id|incident[ _-]?artifact[ _-]?id|mid)\b"
    r")"
)


class ContractError(ValueError):
    pass


def canonical(value) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def digest(value) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def load_json(path: pathlib.Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ContractError(f"cannot read JSON object: {path}") from error
    if not isinstance(value, dict):
        raise ContractError(f"JSON document must be an object: {path}")
    return value


def safe_text(value, label, maximum=2000, guard=None):
    if not isinstance(value, str):
        raise ContractError(f"{label} must be text")
    text = " ".join(value.split())
    if not text or len(text) > maximum:
        raise ContractError(f"{label} must contain 1..{maximum} characters")
    if PRIVATE.search(text):
        raise ContractError(f"{label} contains a private source identifier")
    guard = guard or {}
    lowered = text.casefold()
    tokens = [str(item).casefold() for item in guard.get("tokens", []) if str(item)]
    if any(token in lowered for token in tokens):
        raise ContractError(f"{label} contains a protected source token")
    words = re.findall(r"[a-z0-9_]+", lowered)
    observed = {
        " ".join(words[index : index + 4])
        for index in range(max(0, len(words) - 3))
    }
    protected = {
        str(item).casefold()
        for item in guard.get("four_word_ngrams", [])
        if str(item)
    }
    if observed & protected:
        raise ContractError(f"{label} copies a protected source span")
    return text


def valid_content_hash(world: dict) -> bool:
    expected = world.get("content_sha256")
    if not isinstance(expected, str) or not SHA256.fullmatch(expected):
        return False
    return digest({key: value for key, value in world.items() if key != "content_sha256"}) == expected


def validate_spec(spec: dict, guard=None):
    guard = guard or {}
    allowed = {
        "schema",
        "source_kind",
        "selection_mode",
        "source_binding_sha256",
        "incident_status",
        "cutoff",
        "causal_gold_verified",
        "release_gates",
        "evidence",
        "alternatives",
    }
    if set(spec) != allowed:
        raise ContractError("abstract specification contains missing or unknown fields")
    if spec.get("schema") != SPEC_SCHEMA:
        raise ContractError(f"schema must be {SPEC_SCHEMA}")
    if spec.get("source_kind") != "logview-health-incident":
        raise ContractError("source_kind must be logview-health-incident")
    if spec.get("selection_mode") not in {"named-t", "authorized-experiment"}:
        raise ContractError("selection_mode must be named-t or authorized-experiment")
    binding = spec.get("source_binding_sha256")
    if not isinstance(binding, str) or not SHA256.fullmatch(binding):
        raise ContractError("source_binding_sha256 must be a lowercase SHA-256")
    if spec.get("incident_status") not in {"closed", "resolved"}:
        raise ContractError("incident_status must be closed or resolved")
    if spec.get("causal_gold_verified") is not True:
        raise ContractError("causal_gold_verified must be true")
    cutoff = spec.get("cutoff")
    if not isinstance(cutoff, int) or isinstance(cutoff, bool) or cutoff <= 0:
        raise ContractError("cutoff must be a positive integer")
    gates = spec.get("release_gates")
    required_gates = {"identity_safety", "confidentiality_safety", "technical_fidelity"}
    if not isinstance(gates, dict) or set(gates) != required_gates:
        raise ContractError("release_gates must contain exactly the three required gates")
    if any(gates[name] != "PASS" for name in required_gates):
        raise ContractError("every release gate must PASS")

    evidence = spec.get("evidence")
    if not isinstance(evidence, list) or len(evidence) < 2:
        raise ContractError("evidence must contain at least two fictional items")
    allowed_evidence = {"id", "kind", "source_family", "summary", "available_at"}
    identities, families, normalized = set(), set(), []
    for index, item in enumerate(evidence):
        if not isinstance(item, dict) or set(item) != allowed_evidence:
            raise ContractError("each evidence item must contain exactly the required fields")
        identity = safe_text(item["id"], f"evidence[{index}].id", 120, guard)
        if identity in identities:
            raise ContractError("evidence identities must be unique")
        identities.add(identity)
        when = item["available_at"]
        if not isinstance(when, int) or isinstance(when, bool) or when > cutoff:
            raise ContractError("evidence timestamp is invalid or post-cutoff")
        family = safe_text(item["source_family"], f"evidence[{index}].source_family", 80, guard)
        families.add(family)
        normalized.append(
            {
                "id": identity,
                "kind": safe_text(item["kind"], f"evidence[{index}].kind", 80, guard),
                "source_family": family,
                "summary": safe_text(item["summary"], f"evidence[{index}].summary", 2000, guard),
                "available_at": when,
            }
        )
    if len(families) < 2:
        raise ContractError("evidence must span at least two source families")

    alternatives = spec.get("alternatives")
    if not isinstance(alternatives, list) or len(alternatives) < 2:
        raise ContractError("at least two plausible alternatives are required")
    allowed_alternative = {
        "name", "reason", "source_families", "killing_evidence_ids"
    }
    normalized_alternatives = []
    covered_families = set()
    for index, item in enumerate(alternatives):
        if not isinstance(item, dict) or set(item) != allowed_alternative:
            raise ContractError("each alternative must contain exactly the required fields")
        name = item["name"]
        if not isinstance(name, str) or not NAME.fullmatch(name):
            raise ContractError("alternative name must be a safe identifier")
        source_families = item["source_families"]
        killing = item["killing_evidence_ids"]
        if (
            not isinstance(source_families, list)
            or not source_families
            or any(family not in families for family in source_families)
        ):
            raise ContractError("alternative source_families must reference evidence families")
        if (
            not isinstance(killing, list)
            or not killing
            or any(identity not in identities for identity in killing)
        ):
            raise ContractError("alternative killing evidence must reference evidence items")
        covered_families.update(source_families)
        normalized_alternatives.append(
            {
                "name": name,
                "reason": safe_text(item["reason"], f"alternatives[{index}].reason", 2000, guard),
                "source_families": sorted(set(source_families)),
                "killing_evidence_ids": list(dict.fromkeys(killing)),
            }
        )
    if len(covered_families) < 2:
        raise ContractError("alternatives must span at least two source families")
    return cutoff, normalized, normalized_alternatives


def build(spec: dict, output: pathlib.Path, *, guard=None) -> dict:
    guard = guard or {}
    cutoff, evidence, alternatives = validate_spec(spec, guard)
    token_map = {item["id"]: f"E{index + 1:04d}" for index, item in enumerate(evidence)}
    projected = [
        {
            "token": token_map[item["id"]],
            "kind": item["kind"],
            "source_family": item["source_family"],
            "summary": item["summary"],
            "available_at": item["available_at"],
        }
        for item in evidence
    ]
    branches = [
        {
            "name": item["name"],
            "reason": item["reason"],
            "source_families": item["source_families"],
            "killing_evidence_tokens": [token_map[value] for value in item["killing_evidence_ids"]],
        }
        for item in alternatives
    ]
    world = {
        "schema": WORLD_SCHEMA,
        "source_kind": "logview-health-incident",
        "selection_mode": spec["selection_mode"],
        "cutoff": cutoff,
        "evidence": projected,
        "candidate_branches": branches,
        "release_gates": dict(spec["release_gates"]),
    }
    world["content_sha256"] = digest(world)

    scout_documents = {}
    for role in SCOUT_ROLES:
        scout = {
            "schema": "oaoa.incident-scout-input.v1",
            "role": role,
            "incident_world_sha256": world["content_sha256"],
            "cutoff": cutoff,
            "evidence": projected,
            "candidate_branches": branches,
        }
        scout["content_sha256"] = digest(scout)
        scout_documents[role] = scout

    receipt = {
        "schema": "oaoa.incident-world-build-receipt.v1",
        "status": "PASS",
        "source_kind": "logview-health-incident",
        "selection_mode": spec["selection_mode"],
        "source_binding_sha256": spec["source_binding_sha256"],
        "identifier_guard_sha256": digest(guard),
        "incident_world_sha256": world["content_sha256"],
        "scout_roles": list(SCOUT_ROLES),
        "scout_input_sha256": {
            role: document["content_sha256"] for role, document in scout_documents.items()
        },
        "private_evidence_token_map": token_map,
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "scouts").mkdir(exist_ok=True)
    (output / "incident_world.json").write_bytes(canonical(world) + b"\n")
    for role, document in scout_documents.items():
        (output / "scouts" / f"{role}.json").write_bytes(canonical(document) + b"\n")
    (output / "build_receipt.json").write_bytes(canonical(receipt) + b"\n")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--abstract-spec", required=True, type=pathlib.Path)
    parser.add_argument("--out", required=True, type=pathlib.Path)
    parser.add_argument("--guard", required=True, type=pathlib.Path)
    args = parser.parse_args()
    try:
        receipt = build(
            load_json(args.abstract_spec), args.out, guard=load_json(args.guard)
        )
    except ContractError as error:
        print(f"BLOCKED: {error}", file=sys.stderr)
        return 1
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

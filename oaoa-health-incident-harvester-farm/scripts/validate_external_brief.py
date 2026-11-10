#!/usr/bin/env python3
"""Fail-closed source-safety checks for a Health Incident Harvester brief."""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys


ALLOWED = {
    "schema_version",
    "title",
    "idea",
    "why_hard",
    "proposed_test_shape",
    "anti_cheat_notes",
    "required_evidence",
    "difficulty_hypothesis",
}
REQUIRED = ALLOWED - {"difficulty_hypothesis"}
PRIVATE = re.compile(
    r"(?ix)(?:"
    r"\b[STDP]\d{5,}\b|"
    r"https?://\S*(?:internalfb|internalmeta|tfbnw|facebook)\S*|"
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b|"
    r"\b[0-9a-f]{32}\b|"
    r"\b(?:health[ _-]?incident|logview|opsmate|ace|trajectory|"
    r"experiment[ _-]?id|session[ _-]?id|prompt[ _-]?id|grader[ _-]?id|"
    r"run[ _-]?id|incident[ _-]?artifact[ _-]?id|mid)\b"
    r")"
)


class ValidationError(ValueError):
    pass


def load_object(path: pathlib.Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValidationError(f"cannot read JSON object: {path}") from error
    if not isinstance(value, dict):
        raise ValidationError(f"JSON document must be an object: {path}")
    return value


def flattened_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from flattened_strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from flattened_strings(item)


def validate_shape(brief: dict) -> None:
    unknown = sorted(set(brief) - ALLOWED)
    missing = sorted(REQUIRED - set(brief))
    if unknown:
        raise ValidationError(f"unknown fields: {', '.join(unknown)}")
    if missing:
        raise ValidationError(f"missing fields: {', '.join(missing)}")
    if brief.get("schema_version") != 1:
        raise ValidationError("schema_version must be 1")
    evidence = brief.get("required_evidence")
    if not isinstance(evidence, list) or not evidence or len(evidence) > 20:
        raise ValidationError("required_evidence must contain 1..20 strings")
    for key, value in brief.items():
        if key == "schema_version":
            continue
        values = value if key == "required_evidence" else [value]
        if any(not isinstance(item, str) or not item.strip() for item in values):
            raise ValidationError(f"{key} must contain non-empty text")


def validate_text(brief: dict, guard: dict) -> None:
    tokens = [str(item).casefold() for item in guard.get("tokens", []) if str(item)]
    ngrams = {
        str(item).casefold() for item in guard.get("four_word_ngrams", []) if str(item)
    }
    for text in flattened_strings(brief):
        if PRIVATE.search(text):
            raise ValidationError("brief contains a private source identifier or system name")
        if any(line.lstrip().startswith("# ") for line in text.splitlines()):
            raise ValidationError("brief contains a Markdown section injection")
        lowered = text.casefold()
        if any(token in lowered for token in tokens):
            raise ValidationError("brief contains a protected source token")
        words = re.findall(r"[a-z0-9_]+", lowered)
        observed = {
            " ".join(words[index : index + 4])
            for index in range(max(0, len(words) - 3))
        }
        if observed & ngrams:
            raise ValidationError("brief copies a protected four-word source span")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("brief", type=pathlib.Path)
    parser.add_argument("--guard", required=True, type=pathlib.Path)
    args = parser.parse_args()
    try:
        brief = load_object(args.brief)
        guard = load_object(args.guard)
        validate_shape(brief)
        validate_text(brief, guard)
    except ValidationError as error:
        print(f"BLOCKED: {error}", file=sys.stderr)
        return 1
    print("PASS: source-safe external brief shape and leak checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

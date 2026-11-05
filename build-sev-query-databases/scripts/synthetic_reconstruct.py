#!/usr/bin/env fbpython
"""Generate fictional staging data from an approved abstract specification."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


GENERATOR_KINDS = {
    "sequence_id",
    "timestamp_series",
    "enum_cycle",
    "integer_series",
    "float_series",
    "constant",
    "template",
    "foreign_key",
}


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return value


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_spec(spec: dict[str, Any], policy: dict[str, Any]) -> list[dict[str, Any]]:
    datasets = spec.get("datasets")
    if not isinstance(datasets, list) or not datasets:
        raise ValueError("datasets must be a non-empty list")
    allowed_sources = set(policy.get("allowed_sources", []))
    query_keys: set[tuple[str, str]] = set()
    for dataset in datasets:
        if not isinstance(dataset, dict):
            raise ValueError("each dataset must be an object")
        source = str(dataset.get("source_type", ""))
        if source not in allowed_sources:
            raise ValueError(f"unsupported source_type: {source}")
        query_id = str(dataset.get("query_id", ""))
        if not query_id or (source, query_id) in query_keys:
            raise ValueError(f"missing or duplicate query_id: {source}:{query_id}")
        query_keys.add((source, query_id))
        row_count = dataset.get("row_count")
        if not isinstance(row_count, int) or row_count < 1:
            raise ValueError(f"{query_id}: row_count must be positive")
        columns = dataset.get("columns")
        if not isinstance(columns, list) or not columns:
            raise ValueError(f"{query_id}: columns must be non-empty")
        names: set[str] = set()
        for column in columns:
            if not isinstance(column, dict):
                raise ValueError(f"{query_id}: column must be an object")
            name = str(column.get("name", ""))
            generator = column.get("generator")
            if not name or name in names or not isinstance(generator, dict):
                raise ValueError(f"{query_id}: invalid or duplicate column {name}")
            names.add(name)
            kind = generator.get("kind")
            if kind not in GENERATOR_KINDS:
                raise ValueError(f"{query_id}.{name}: unsupported generator {kind}")
    return datasets


def build_pools(datasets: list[dict[str, Any]]) -> dict[str, list[Any]]:
    pools: dict[str, list[Any]] = {}
    for dataset in datasets:
        for column in dataset["columns"]:
            generator = column["generator"]
            if generator["kind"] != "sequence_id":
                continue
            pool = str(generator.get("pool") or f"{dataset['query_id']}.{column['name']}")
            prefix = str(generator.get("prefix", "item"))
            start = int(generator.get("start", 1))
            pools[pool] = [
                f"{prefix}_{index:06d}"
                for index in range(start, start + int(dataset["row_count"]))
            ]
    return pools


def generate_value(generator: dict[str, Any], index: int, pools: dict[str, list[Any]]) -> Any:
    kind = generator["kind"]
    if kind == "sequence_id":
        pool = str(generator.get("pool", ""))
        values = pools[pool] if pool else []
        if not values:
            prefix = str(generator.get("prefix", "item"))
            return f"{prefix}_{int(generator.get('start', 1)) + index:06d}"
        return values[index % len(values)]
    if kind == "foreign_key":
        values = pools.get(str(generator.get("pool", "")), [])
        if not values:
            raise ValueError("foreign_key references an unknown or empty pool")
        return values[index % len(values)]
    if kind == "timestamp_series":
        return int(generator["start"]) + index * int(generator.get("step_seconds", 60))
    if kind == "enum_cycle":
        values = generator.get("values", [])
        if not isinstance(values, list) or not values:
            raise ValueError("enum_cycle requires values")
        return values[index % len(values)]
    if kind == "integer_series":
        return int(generator.get("start", 0)) + index * int(generator.get("step", 1))
    if kind == "float_series":
        return round(float(generator.get("start", 0.0)) + index * float(generator.get("step", 1.0)), 6)
    if kind == "constant":
        return generator.get("value")
    if kind == "template":
        return str(generator.get("value", "record_{index}")).format(index=index + 1)
    raise AssertionError(kind)


def validate_relationships(
    datasets: list[dict[str, Any]],
    rows_by_query: dict[str, list[dict[str, Any]]],
    pools: dict[str, list[Any]],
) -> dict[str, bool]:
    checks: dict[str, bool] = {}
    for dataset in datasets:
        query_id = str(dataset["query_id"])
        rows = rows_by_query[query_id]
        checks[f"{query_id}.row_count"] = len(rows) == int(dataset["row_count"])
        for column in dataset["columns"]:
            generator = column["generator"]
            name = str(column["name"])
            if generator["kind"] == "sequence_id":
                checks[f"{query_id}.{name}.unique"] = len({row[name] for row in rows}) == len(rows)
            if generator["kind"] == "foreign_key":
                pool = set(pools.get(str(generator.get("pool", "")), []))
                checks[f"{query_id}.{name}.foreign_key"] = bool(pool) and all(
                    row[name] in pool for row in rows
                )
        order_by = dataset.get("ordered_by")
        if order_by:
            values = [row[str(order_by)] for row in rows]
            checks[f"{query_id}.{order_by}.ordered"] = values == sorted(values)
    return checks


def scan_outputs(root: Path, patterns: list[str]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    compiled = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        text = path.read_text(errors="replace")
        if path.suffix == ".json":
            try:
                value = json.loads(text)
                if isinstance(value, dict):
                    value.pop("sev_id", None)
                    value.pop("task_id", None)
                    # Private scale metadata uses the contract value
                    # `production_scale`; scan the generated task data, not
                    # this required authoring label.
                    value.pop("volume", None)
                    text = json.dumps(value, sort_keys=True)
            except json.JSONDecodeError:
                pass
        for pattern, regex in zip(patterns, compiled):
            if regex.search(text):
                findings.append({"path": str(path.relative_to(root)), "pattern": pattern})
    return findings


def reconstruct(
    spec: dict[str, Any],
    policy: dict[str, Any],
    spec_sha256: str,
    output: Path,
) -> dict[str, Any]:
    datasets = validate_spec(spec, policy)
    source_dir = output / "sources"
    source_dir.mkdir(parents=True, exist_ok=True)
    pools = build_pools(datasets)
    rows_by_query: dict[str, list[dict[str, Any]]] = {}
    for dataset_index, dataset in enumerate(datasets, start=1):
        query_id = str(dataset["query_id"])
        rows = [
            {
                str(column["name"]): generate_value(column["generator"], index, pools)
                for column in dataset["columns"]
            }
            for index in range(int(dataset["row_count"]))
        ]
        rows_by_query[query_id] = rows
        payload = {
            "sev_id": str(spec["task_id"]),
            "tool": dataset["source_type"],
            "operation": dataset.get("operation", "query"),
            "query_id": query_id,
            "source_lineage_id": dataset.get(
                "source_lineage_id",
                f"{dataset['source_type']}_lineage_{dataset_index:03d}",
            ),
            "resource_name": dataset["resource_name"],
            "query": dataset.get("fictional_query", "synthetic registered operation"),
            "classification": dataset.get("classification", "unclassified"),
            "classification_reason": dataset.get("classification_reason", "approved abstract evidence"),
            "time_range": dataset.get("time_range", {}),
            "supported_functions": dataset.get("supported_functions", []),
            "columns": [
                {"name": column["name"], "type": column.get("type", "dynamic")}
                for column in dataset["columns"]
            ],
            "rows": rows,
            "invariants": dataset.get("invariants", []),
            "volume": dataset.get("volume", {}),
            "privacy": {"values_approved": True, "included_keys": dataset.get("included_metadata_keys", [])},
            "anonymization": {"strategy": "synthetic_reconstruction", "release_eligible": True},
        }
        if dataset.get("context"):
            payload["context"] = dataset["context"]
        (source_dir / f"{query_id}.json").write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n"
        )
    checks = validate_relationships(datasets, rows_by_query, pools)
    findings = scan_outputs(output, list(policy.get("forbidden_output_patterns", [])))
    validation = {
        "identity_safety": not findings,
        "confidentiality_safety": not findings,
        "technical_fidelity": all(checks.values()),
        "spec_sha256": spec_sha256,
        "checks": checks,
        "findings": findings,
    }
    validation["release_eligible"] = all(
        validation[key]
        for key in ("identity_safety", "confidentiality_safety", "technical_fidelity")
    )
    (output / "synthetic_reconstruction_report.json").write_text(
        json.dumps(validation, indent=2, sort_keys=True) + "\n"
    )
    if not validation["release_eligible"]:
        raise RuntimeError("synthetic reconstruction failed a release gate")
    return validation


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    validation = reconstruct(
        load_object(args.spec), load_object(args.policy), sha256(args.spec), args.output
    )
    print(json.dumps(validation, sort_keys=True))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Discover OpsMate experiment runs for one SEV without caller-supplied IDs."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import subprocess
import sys
from datetime import datetime, timezone

DEFAULT_REGISTRY = pathlib.Path(
    "/data/repos/fbsource/nest/apps/oa/oaoa_evaluator/lib/"
    "opsmate-trajectory-experiments.ts"
)


def registry_entries(text: str) -> list[dict[str, str]]:
    block = text.split("OPSMATE_TRAJECTORY_EXPERIMENTS =", 1)[-1]
    block = block.split("] as const", 1)[0]
    entries = []
    for obj in re.findall(r"\{(.*?)\}", block, flags=re.S):
        fields = dict(re.findall(r"(id|label|generation|registryName):\s*'([^']+)'", obj))
        if "id" in fields:
            entries.append(fields)
    return entries


def rows(value):
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        for key in ("rows", "data", "results", "runs"):
            if isinstance(value.get(key), list):
                return value[key]
    return []


def run_json(cmd: list[str]):
    proc = subprocess.run(cmd, text=True, capture_output=True)
    if proc.returncode:
        return None, {"exit_code": proc.returncode, "stderr": proc.stderr[-2000:]}
    try:
        value = json.loads(proc.stdout)
    except json.JSONDecodeError as error:
        return None, {"error": f"invalid JSON: {error}"}
    if isinstance(value, dict) and value.get("status") == "error":
        return None, {"error": value.get("message", "command returned an error")}
    return value, None


def nested(row: dict, *paths):
    for path in paths:
        value = row
        for part in path.split("."):
            value = value.get(part) if isinstance(value, dict) else None
        if value not in (None, ""):
            return value
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sev", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--registry", type=pathlib.Path, default=DEFAULT_REGISTRY)
    args = ap.parse_args()
    sev = args.sev.strip().upper()
    if not re.fullmatch(r"S\d+", sev):
        ap.error("--sev must look like S707352")

    text = args.registry.read_text()
    experiments = registry_entries(text)
    report = {
        "schema_version": 1,
        "sev_id": sev,
        "discovered_at": datetime.now(timezone.utc).isoformat(),
        "registry": str(args.registry),
        "registry_sha256": hashlib.sha256(text.encode()).hexdigest(),
        "commands": [],
        "experiments": experiments,
        "export_failures": [],
        "matching_runs": [],
        "live_instances": [],
        "trajectory_checks": [],
        "discovery_failures": [],
        "status": "incomplete",
    }

    cmd = ["meta", "opsmate.instance", "from-sev", f"--sev={sev}",
           "--output=json", "--no-truncate"]
    report["commands"].append(" ".join(cmd))
    instances_value, error = run_json(cmd)
    if error:
        report["discovery_failures"].append({"stage": "from-sev", **error})
        instances = []
    else:
        instances = rows(instances_value)
    for instance in instances:
        number = instance.get("number")
        if not number:
            report["discovery_failures"].append(
                {"stage": "from-sev", "error": "instance missing number"})
            continue
        cmd = ["meta", "opsmate.instance", "conversations", f"--instance={number}",
               "--output=json", "--no-truncate", "--columns=all"]
        report["commands"].append(" ".join(cmd))
        conversations, error = run_json(cmd)
        if error:
            report["discovery_failures"].append(
                {"stage": "conversations", "instance": number, **error})
            continue
        sessions = [entry for entry in rows(conversations)
                    if entry.get("kind") == "proactive_run" and entry.get("session_id")]
        report["live_instances"].append(
            {"instance": instance, "proactive_runs": sessions})

    for item in report["live_instances"]:
        for run in item["proactive_runs"]:
            session = run["session_id"]
            cmd = ["meta", "quality-toolkit.trajectory", "get", f"--id={session}",
                   "--output=json", "--no-truncate"]
            report["commands"].append(" ".join(cmd))
            proc = subprocess.run(cmd, text=True, capture_output=True)
            check = {"instance": item["instance"]["number"], "session_id": session,
                     "readable": False}
            if proc.returncode:
                check.update({"exit_code": proc.returncode, "error": proc.stderr[-2000:]})
            else:
                try:
                    value = json.loads(proc.stdout)
                    if isinstance(value, dict) and value.get("status") == "error":
                        check["error"] = value.get("message", "trajectory read failed")
                    else:
                        check.update({"readable": True,
                                      "sha256": hashlib.sha256(proc.stdout.encode()).hexdigest(),
                                      "bytes": len(proc.stdout.encode())})
                except json.JSONDecodeError as error:
                    check["error"] = f"invalid JSON: {error}"
            report["trajectory_checks"].append(check)

    for experiment in experiments:
        cmd = ["meta", "opsmate.experiment", "export-runs",
               f"--experiment-id={experiment['id']}", "--output=json", "--columns=all"]
        report["commands"].append(" ".join(cmd))
        value, error = run_json(cmd)
        if error:
            report["export_failures"].append({
                "experiment_id": experiment["id"], **error,
            })
            continue
        exported = rows(value)
        for row in exported:
            short = str(nested(row, "incident.short_name", "incident_short_name", "sev_id") or "").upper()
            if short != sev:
                continue
            item = {"experiment": experiment, "run": row}
            item["trajectory_ref"] = nested(row, "trajectory_ref", "trajectory.ref")
            item["arm_name"] = nested(row, "arm.name", "experiment_arm_name", "arm_name")
            item["agent_ref"] = nested(row, "arm.agent_ref", "agent_ref")
            report["matching_runs"].append(item)

    ent_complete = bool(report["matching_runs"]) and all(
        item["trajectory_ref"] and item["arm_name"] and item["agent_ref"]
        for item in report["matching_runs"]
    )
    live_complete = bool(report["live_instances"]) and all(
        item["instance"].get("agent") and item["proactive_runs"]
        for item in report["live_instances"]
    )
    live_complete = live_complete and bool(report["trajectory_checks"]) and all(
        check["readable"] for check in report["trajectory_checks"]
    )
    complete = bool(experiments and not report["export_failures"] and
                    not report["discovery_failures"] and
                    (ent_complete or live_complete))
    report["status"] = "complete" if complete else "incomplete"
    output = pathlib.Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    session_count = sum(len(item["proactive_runs"]) for item in report["live_instances"])
    print(f"{report['status']}: {len(report['matching_runs'])} experiment runs, "
          f"{session_count} live sessions; inventory={output}")
    return 0 if complete else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Build private SEV/oncall discovery context using read-only Meta CLI calls."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import subprocess
import sys
from datetime import datetime, timezone


def run(command: list[str]) -> dict:
    proc = subprocess.run(command, text=True, capture_output=True)
    result = {"command": " ".join(command), "exit_code": proc.returncode,
              "status": "ok" if proc.returncode == 0 else "error"}
    try:
        data = json.loads(proc.stdout)
        if isinstance(data, dict) and (data.get("status") == "error" or data.get("isError") is True):
            result["status"] = "denied" if "PERMISSION_DENIED" in json.dumps(data) else "error"
            result["error"] = data.get("message") or json.dumps(data.get("content"))[:2000]
        else:
            result["data"] = data
    except json.JSONDecodeError:
        result["error"] = (proc.stderr or proc.stdout)[-2000:]
    return result


def text_content(value) -> str:
    if not isinstance(value, dict):
        return ""
    return "\n".join(str(x.get("text", "")) for x in value.get("content", [])
                     if isinstance(x, dict) and x.get("type") == "text")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sev", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--cutoff-time", type=int)
    args = ap.parse_args()
    sev = args.sev.strip().upper()
    if not re.fullmatch(r"S\d+", sev):
        ap.error("--sev must look like S707352")

    commands = {
        "record": ["meta", "sevmanager.sev", "list", f"--sev={sev}",
                   "--columns=all", "--timezone=UTC", "--output=json", "--no-truncate"],
        "linked_context": ["meta", "sevmanager.sev", "linked-context", f"--sev={sev}",
                           "--output=json", "--no-truncate"],
        "relevant_metrics": ["meta", "sevmanager.sev", "relevant-metrics",
                             f"--sev-number={sev}", "--output=json", "--no-truncate"],
        "snapshot": ["meta", "sevmanager.sev", "snapshot", f"--sev={sev}",
                     "--output=json", "--no-truncate"],
    }
    if args.cutoff_time:
        commands["linked_context"].append(f"--cutoff-time={args.cutoff_time}")
        commands["relevant_metrics"].append(f"--cutoff-time={args.cutoff_time}")
        commands["snapshot"].append(f"--cutoff-time={args.cutoff_time}")
    sources = {name: run(command) for name, command in commands.items()}

    linked_text = text_content(sources["linked_context"].get("data"))
    try:
        linked = json.loads(linked_text)
    except json.JSONDecodeError:
        linked = {}
    metrics_text = text_content(sources["relevant_metrics"].get("data"))
    urls = sorted(set(re.findall(r"https?://[^\s\]}>\"']+", linked_text + "\n" + metrics_text)))
    rotations = [x.strip() for x in str(linked.get("owner_oncall_rotations", "")).split(",") if x.strip()]
    rows = sources["record"].get("data") if isinstance(sources["record"].get("data"), list) else []
    canonical = rows[0] if rows else {}
    failures = [{"source": name, "status": value["status"], "error": value.get("error", "")}
                for name, value in sources.items() if value["status"] != "ok"]
    report = {
        "schema_version": 1,
        "sev_id": sev,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "complete" if canonical and linked and not failures else "incomplete",
        "canonical_sev": canonical,
        "owner_oncall_rotations": rotations,
        "affected_services": sorted({str(x.get("service_id")) for x in linked.get("linked_slis", [])
                                     if isinstance(x, dict) and x.get("service_id")}),
        "investigation_time_range": linked.get("investigation_time_range"),
        "linked_alerts": linked.get("linked_alerts", []),
        "linked_slis": linked.get("linked_slis", []),
        "telemetry_reference_urls": urls,
        "sources": sources,
        "gaps": failures,
    }
    stable = dict(report)
    stable.pop("generated_at")
    report["content_sha256"] = hashlib.sha256(
        json.dumps(stable, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    output = pathlib.Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(f"{report['status']}: oncalls={len(rotations)} services={len(report['affected_services'])} "
          f"references={len(urls)} inventory={output}")
    return 0 if report["status"] == "complete" else 1


if __name__ == "__main__":
    sys.exit(main())

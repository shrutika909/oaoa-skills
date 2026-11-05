#!/usr/bin/env fbpython
"""Discover database evidence calls from every OpsMate trajectory for a SEV."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any


TOOLS = ("scuba", "hive", "daiquery", "presto", "logview")


def run_meta(*arguments: str) -> Any:
    result = subprocess.run(
        ["meta", *arguments, "--output=json", "--no-truncate"],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def detect_tool(name: str, arguments: Any) -> str | None:
    text = f"{name} {json.dumps(arguments, sort_keys=True)}".lower()
    return next((tool for tool in TOOLS if tool in text), None)


def discover(sev: str, output: Path, fixture: Path | None = None) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    trajectories = output / "trajectories"
    calls_dir = output / "private_calls"
    trajectories.mkdir(exist_ok=True)
    calls_dir.mkdir(exist_ok=True)
    instances = json.loads(fixture.read_text())["instances"] if fixture else run_meta(
        "opsmate.instance", "from-sev", f"--sev={sev}"
    )
    inventory: list[dict[str, Any]] = []
    trajectory_records: list[dict[str, Any]] = []
    inaccessible: list[dict[str, Any]] = []
    for instance in instances:
        number = str(instance["number"])
        conversations = instance.get("conversations") if fixture else run_meta(
            "opsmate.instance", "conversations", f"--instance={number}"
        )
        for conversation in conversations.get("data", []):
            session = conversation.get("session_id")
            if not session or conversation.get("kind") not in {"proactive_run", "adhoc_conversation"}:
                continue
            try:
                trajectory = conversation.get("trajectory") if fixture else run_meta(
                    "opsmate.instance",
                    "trajectory",
                    f"--instance={number}",
                    f"--session={session}",
                    "--char-budget=1000000",
                )
            except subprocess.CalledProcessError as error:
                inaccessible.append(
                    {"instance": number, "session_id": session, "stage": "trajectory", "error": error.stderr.strip()}
                )
                continue
            events = []
            for row in trajectory.get("rows", []):
                for call in row.get("tool_calls") or []:
                    initial_tool = detect_tool(
                        str(call.get("name", "")), call.get("arguments", {})
                    )
                    call_name = str(call.get("name", "")).lower()
                    executable = call_name == "bash" or any(
                        marker in call_name for marker in ("scuba", "hive", "daiquery", "presto", "logview")
                    )
                    if not initial_tool or not executable:
                        continue
                    try:
                        detail = call.get("detail") if fixture else run_meta(
                            "opsmate.instance",
                            "trajectory",
                            f"--instance={number}",
                            f"--session={session}",
                            f"--call={call['id']}",
                        ).get("call", {})
                    except subprocess.CalledProcessError as error:
                        inaccessible.append(
                            {"instance": number, "session_id": session, "call_id": call.get("id"), "stage": "call", "error": error.stderr.strip()}
                        )
                        continue
                    tool = detect_tool(str(detail.get("name", call.get("name", ""))), detail.get("arguments", call.get("arguments", {}))) or initial_tool
                    if not tool:
                        continue
                    call_id = str(detail.get("id", call["id"]))
                    (calls_dir / f"{call_id}.json").write_text(
                        json.dumps(detail, indent=2, sort_keys=True) + "\n"
                    )
                    event = {
                        "tool": tool,
                        "operation": "trajectory_call",
                        "arguments": detail.get("arguments", {}),
                        "call_id": call_id,
                        "turn": detail.get("turn", row.get("turn")),
                        "status": "observed",
                    }
                    events.append(event)
                    inventory.append(
                        {
                            "tool": tool,
                            "instance": number,
                            "agent": instance.get("agent"),
                            "session_id": session,
                            "call_id": call_id,
                            "turn": event["turn"],
                            "private_call_path": f"private_calls/{call_id}.json",
                        }
                    )
            record = {
                "trajectory_id": session,
                "harness": instance.get("agent", "unknown"),
                "cutoff": conversation.get("updated") or conversation.get("time"),
                "events": events,
            }
            (trajectories / f"{number}_{session}.json").write_text(
                json.dumps(record, indent=2, sort_keys=True) + "\n"
            )
            trajectory_records.append(record)
    result = {
        "schema_version": "1.0",
        "sev_id": sev,
        "instances": len(instances),
        "trajectories": len(trajectory_records),
        "database_calls": inventory,
        "included_tools": sorted({item["tool"] for item in inventory}),
        "missing_tools": sorted(set(TOOLS) - {item["tool"] for item in inventory}),
        "inaccessible": inaccessible,
        "status": "complete_with_gaps" if inventory and inaccessible else "complete" if inventory else "blocked_no_database_calls",
    }
    (output / "source_inventory.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sev", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--fixture", type=Path)
    args = parser.parse_args()
    result = discover(args.sev, args.output, args.fixture)
    print(
        json.dumps(
            {
                "sev_id": result["sev_id"],
                "status": result["status"],
                "instances": result["instances"],
                "trajectories": result["trajectories"],
                "database_call_count": len(result["database_calls"]),
                "included_tools": result["included_tools"],
                "missing_tools": result["missing_tools"],
                "inaccessible_count": len(result["inaccessible"]),
                "inventory_path": str(args.output / "source_inventory.json"),
            },
            sort_keys=True,
        )
    )
    if not result["status"].startswith("complete"):
        raise SystemExit(2)


if __name__ == "__main__":
    main()

#!/usr/bin/env fbpython
"""Autonomously discover a SEV and build a synthetic database scaffold."""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path

from discover_opsmate import discover
from scaffold import Build
from synthetic_reconstruct import load_object, reconstruct, sha256


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sev", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--spec", type=Path)
    parser.add_argument("--discovery-fixture", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    with tempfile.TemporaryDirectory() as temporary:
        work = Path(temporary)
        discovery_dir = work / "discovery"
        inventory = discover(args.sev, discovery_dir, args.discovery_fixture)
        if not inventory["status"].startswith("complete"):
            raise SystemExit("OpsMate contained no database calls to scaffold")
        spec_path = args.spec or work / "fallback_spec.json"
        if args.spec is None:
            spec = load_object(root / "assets" / "fallback_spec_template.json")
            spec["task_id"] = args.sev
            observed = set(inventory["included_tools"])
            spec["datasets"] = [
                dataset for dataset in spec["datasets"] if dataset["source_type"] in observed
            ]
            if "scuba" not in observed:
                for dataset in spec["datasets"]:
                    worker = next(
                        (column for column in dataset["columns"] if column["name"] == "worker_id"),
                        None,
                    )
                    if worker is not None:
                        worker["generator"] = {
                            "kind": "sequence_id",
                            "pool": "workers",
                            "prefix": "worker",
                        }
                        break
            spec["generation"] = {
                "mode": "autonomous_fallback",
                "source_inventory": "OpsMate trajectories",
                "missing_tools": inventory["missing_tools"],
            }
            spec_path.write_text(json.dumps(spec, indent=2, sort_keys=True) + "\n")
        staging = work / "staging"
        staging.mkdir()
        reconstruct(
            load_object(spec_path),
            load_object(root / "assets" / "anonymization-policy.json"),
            sha256(spec_path),
            staging,
        )
        shutil.copytree(discovery_dir / "trajectories", staging / "trajectories")
        shutil.copy2(discovery_dir / "source_inventory.json", staging / "source_inventory.json")
        Build(args.sev, staging, args.output, "export").run()
        private_discovery = args.output / "private" / "discovery"
        shutil.copytree(discovery_dir, private_discovery)
    print(args.output / "scaffolding_summary.json")


if __name__ == "__main__":
    main()

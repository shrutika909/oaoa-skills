#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "registry_gate.py"
SPEC = importlib.util.spec_from_file_location("registry_gate", SCRIPT)
assert SPEC and SPEC.loader
gate = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = gate
SPEC.loader.exec_module(gate)


class RegistryGateTest(unittest.TestCase):
    def clear_checks(self) -> dict[str, str]:
        return {
            "repository": "clear",
            "cards": "clear",
            "retired_tasks": "clear",
            "rejected_tasks": "clear",
            "semantic_dedupe": "clear",
        }

    def test_confirmed_fenced_claim_allows_remote_intake(self) -> None:
        result = gate.evaluate(
            {
                "schema_version": "oaoa.health-incident-registry-gate.v1",
                "stable_source_key_sha256": "a" * 64,
                "registry": {
                    "status": "claimed",
                    "fenced_claim_receipt_sha256": "b" * 64,
                },
                "dedupe_checks": self.clear_checks(),
            }
        )

        self.assertEqual(result["status"], "FENCED_CLAIM_CONFIRMED")
        self.assertTrue(result["private_research_allowed"])
        self.assertTrue(result["local_prototype_allowed"])
        self.assertTrue(result["external_intake_allowed"])

    def test_registry_outage_allows_local_work_only(self) -> None:
        result = gate.evaluate(
            {
                "schema_version": "oaoa.health-incident-registry-gate.v1",
                "stable_source_key_sha256": "a" * 64,
                "registry": {
                    "status": "unavailable",
                    "attempt_receipt_sha256": "c" * 64,
                },
                "dedupe_checks": self.clear_checks(),
            }
        )

        self.assertEqual(
            result["status"], "REGISTRY_UNAVAILABLE_CONTINUING_LOCAL"
        )
        self.assertTrue(result["private_research_allowed"])
        self.assertTrue(result["local_prototype_allowed"])
        self.assertFalse(result["external_intake_allowed"])
        self.assertFalse(result["publication_allowed"])
        self.assertFalse(result["submission_allowed"])

    def test_known_conflict_blocks_all_work(self) -> None:
        checks = self.clear_checks()
        checks["cards"] = "conflict"
        result = gate.evaluate(
            {
                "schema_version": "oaoa.health-incident-registry-gate.v1",
                "stable_source_key_sha256": "a" * 64,
                "registry": {"status": "unavailable", "attempt_receipt_sha256": "c" * 64},
                "dedupe_checks": checks,
            }
        )

        self.assertEqual(result["status"], "KNOWN_DUPLICATE_BLOCKED")
        self.assertFalse(result["private_research_allowed"])
        self.assertFalse(result["local_prototype_allowed"])

    def test_missing_dedupe_check_fails_closed(self) -> None:
        checks = self.clear_checks()
        del checks["semantic_dedupe"]

        with self.assertRaisesRegex(gate.GateError, "semantic_dedupe"):
            gate.evaluate(
                {
                    "schema_version": "oaoa.health-incident-registry-gate.v1",
                    "stable_source_key_sha256": "a" * 64,
                    "registry": {
                        "status": "unavailable",
                        "attempt_receipt_sha256": "c" * 64,
                    },
                    "dedupe_checks": checks,
                }
            )

    def test_claim_without_fenced_receipt_fails_closed(self) -> None:
        with self.assertRaisesRegex(gate.GateError, "fenced_claim_receipt_sha256"):
            gate.evaluate(
                {
                    "schema_version": "oaoa.health-incident-registry-gate.v1",
                    "stable_source_key_sha256": "a" * 64,
                    "registry": {"status": "claimed"},
                    "dedupe_checks": self.clear_checks(),
                }
            )


if __name__ == "__main__":
    unittest.main()

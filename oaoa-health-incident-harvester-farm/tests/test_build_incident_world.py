import importlib.util
import json
import pathlib
import tempfile
import unittest


SCRIPT = pathlib.Path(__file__).parents[1] / "scripts" / "build_incident_world.py"
SPEC = importlib.util.spec_from_file_location("build_incident_world", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def valid_spec():
    return {
        "schema": "oaoa.health-incident-abstract-spec.v1",
        "source_kind": "logview-health-incident",
        "selection_mode": "named-t",
        "source_binding_sha256": "a" * 64,
        "incident_status": "resolved",
        "cutoff": 200,
        "causal_gold_verified": True,
        "release_gates": {
            "identity_safety": "PASS",
            "confidentiality_safety": "PASS",
            "technical_fidelity": "PASS",
        },
        "evidence": [
            {
                "id": "fictional-event-1",
                "kind": "event",
                "source_family": "operator-events",
                "summary": "Upstream work resumes while downstream dispatch remains paused.",
                "available_at": 110,
            },
            {
                "id": "fictional-state-2",
                "kind": "state",
                "source_family": "coordination-state",
                "summary": "A retained lease epoch differs from the active controller epoch.",
                "available_at": 120,
            },
            {
                "id": "fictional-metric-3",
                "kind": "metric",
                "source_family": "worker-metrics",
                "summary": "Worker capacity remains available during the dispatch pause.",
                "available_at": 130,
            },
        ],
        "alternatives": [
            {
                "name": "capacity_exhaustion",
                "reason": "Paused dispatch can resemble exhausted workers.",
                "source_families": ["worker-metrics", "operator-events"],
                "killing_evidence_ids": ["fictional-metric-3"],
            },
            {
                "name": "dependency_outage",
                "reason": "A downstream dependency failure can also stop dispatch.",
                "source_families": ["operator-events", "coordination-state"],
                "killing_evidence_ids": ["fictional-event-1", "fictional-state-2"],
            },
        ],
    }


class BuildIncidentWorldTest(unittest.TestCase):
    def test_builds_hash_bound_world_and_exactly_two_scout_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            output = pathlib.Path(directory)
            result = MODULE.build(valid_spec(), output)
            self.assertEqual(result["status"], "PASS")
            world = json.loads((output / "incident_world.json").read_text())
            self.assertEqual(world["schema"], "oaoa.agent-incident-world.v1")
            self.assertTrue(MODULE.valid_content_hash(world))
            scouts = sorted((output / "scouts").glob("*.json"))
            self.assertEqual([path.stem for path in scouts], ["directional", "misleading"])
            self.assertNotIn("source_binding_sha256", json.dumps(world))

    def test_rejects_private_identifiers_and_post_cutoff_evidence(self):
        for mutation in ("private", "post_cutoff"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                spec = valid_spec()
                if mutation == "private":
                    spec["evidence"][0]["summary"] += " T707541"
                else:
                    spec["evidence"][0]["available_at"] = 201
                with self.assertRaises(MODULE.ContractError):
                    MODULE.build(spec, pathlib.Path(directory))

    def test_requires_all_release_gates_and_two_source_backed_alternatives(self):
        variants = []
        missing_gate = valid_spec()
        missing_gate["release_gates"]["confidentiality_safety"] = "FAIL"
        variants.append(missing_gate)
        one_alternative = valid_spec()
        one_alternative["alternatives"] = one_alternative["alternatives"][:1]
        variants.append(one_alternative)
        one_family = valid_spec()
        for evidence in one_family["evidence"]:
            evidence["source_family"] = "one-family"
        variants.append(one_family)
        for spec in variants:
            with self.subTest(spec=spec), tempfile.TemporaryDirectory() as directory:
                with self.assertRaises(MODULE.ContractError):
                    MODULE.build(spec, pathlib.Path(directory))

    def test_rejects_unknown_top_level_source_payload(self):
        spec = valid_spec()
        spec["raw_trajectory"] = {"private": "payload"}
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(MODULE.ContractError):
                MODULE.build(spec, pathlib.Path(directory))

    def test_rejects_source_specific_token_and_ngram_before_scouting(self):
        guards = (
            ({"tokens": ["retained lease epoch"]}, "retained lease epoch"),
            ({"four_word_ngrams": ["upstream work resumes while"]}, "upstream work resumes while"),
        )
        for guard, _ in guards:
            with self.subTest(guard=guard), tempfile.TemporaryDirectory() as directory:
                with self.assertRaises(MODULE.ContractError):
                    MODULE.build(valid_spec(), pathlib.Path(directory), guard=guard)


if __name__ == "__main__":
    unittest.main()

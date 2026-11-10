import hashlib
import importlib.util
import json
import pathlib
import tempfile
import unittest


SCRIPT = pathlib.Path(__file__).parents[1] / "scripts" / "validate_scout_runs.py"
SPEC = importlib.util.spec_from_file_location("validate_scout_runs", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ValidateScoutRunsTest(unittest.TestCase):
    def fixture(self, root):
        outputs = {}
        for role in ("directional", "misleading"):
            path = root / f"{role}.json"
            path.write_text(json.dumps({"role": role, "findings": ["E0001"]}))
            outputs[role] = path
        build = {
            "status": "PASS",
            "incident_world_sha256": "a" * 64,
            "scout_roles": ["directional", "misleading"],
            "scout_input_sha256": {"directional": "b" * 64, "misleading": "c" * 64},
        }
        runs = {
            "schema": "oaoa.incident-scout-runs.v1",
            "incident_world_sha256": "a" * 64,
            "runs": [
                {
                    "role": role,
                    "status": "PASS",
                    "session_id": f"session-{index}",
                    "provider": "meta",
                    "model": "approved-model",
                    "input_sha256": build["scout_input_sha256"][role],
                    "output_path": str(outputs[role]),
                    "output_sha256": sha(outputs[role]),
                }
                for index, role in enumerate(("directional", "misleading"), 1)
            ],
        }
        return build, runs

    def test_accepts_exactly_two_independent_bound_runs(self):
        with tempfile.TemporaryDirectory() as directory:
            build, runs = self.fixture(pathlib.Path(directory))
            receipt = MODULE.validate(build, runs)
            self.assertEqual(receipt["status"], "PASS")

    def test_rejects_duplicate_session_failed_or_tampered_output(self):
        mutations = ("duplicate", "failed", "tampered")
        for mutation in mutations:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                root = pathlib.Path(directory)
                build, runs = self.fixture(root)
                if mutation == "duplicate":
                    runs["runs"][1]["session_id"] = runs["runs"][0]["session_id"]
                elif mutation == "failed":
                    runs["runs"][1]["status"] = "FAIL"
                else:
                    pathlib.Path(runs["runs"][1]["output_path"]).write_text("tampered")
                with self.assertRaises(MODULE.ContractError):
                    MODULE.validate(build, runs)


if __name__ == "__main__":
    unittest.main()

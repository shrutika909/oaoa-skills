import importlib.util
import pathlib
import unittest


SCRIPT = pathlib.Path(__file__).parents[1] / "scripts" / "validate_external_brief.py"
SPEC = importlib.util.spec_from_file_location("validate_external_brief", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def valid_brief():
    return {
        "schema_version": 1,
        "title": "Recover a stalled regional worker fleet",
        "idea": "Diagnose a partial recovery where upstream work resumes but downstream workers remain paused until their stale coordination state is reconciled.",
        "why_hard": "Several plausible symptoms overlap, and the operator must distinguish stale coordination from capacity and dependency failures.",
        "proposed_test_shape": "Provide deterministic fictional event streams, bounded operator commands, decoys, and held-out recovery assertions.",
        "anti_cheat_notes": "Keep the causal mapping and decisive event sequence outside the candidate image while exposing fair falsifying evidence.",
        "required_evidence": ["The initial state reproduces the partial recovery", "The final state proves downstream progress"],
    }


class ValidateExternalBriefTest(unittest.TestCase):
    def test_accepts_source_safe_brief(self):
        MODULE.validate_shape(valid_brief())
        MODULE.validate_text(valid_brief(), {})

    def test_rejects_health_incident_source_classes(self):
        unsafe = (
            "T707541",
            "health incident 99123",
            "LogView checkout_errors",
            "OpsMate result",
            "0123456789abcdef0123456789abcdef",
            "123e4567-e89b-12d3-a456-426614174000",
            "session_id=secret",
        )
        for value in unsafe:
            with self.subTest(value=value):
                brief = valid_brief()
                brief["idea"] += " " + value
                with self.assertRaises(MODULE.ValidationError):
                    MODULE.validate_text(brief, {})

    def test_rejects_protected_token_and_four_word_span(self):
        guard = {
            "tokens": ["privateService42"],
            "four_word_ngrams": ["rare failure phrase copied"],
        }
        for value in ("privateService42", "rare failure phrase copied"):
            with self.subTest(value=value):
                brief = valid_brief()
                brief["idea"] += " " + value
                with self.assertRaises(MODULE.ValidationError):
                    MODULE.validate_text(brief, guard)

    def test_rejects_unknown_fields_and_heading_injection(self):
        brief = valid_brief()
        brief["source_id"] = "opaque"
        with self.assertRaises(MODULE.ValidationError):
            MODULE.validate_shape(brief)
        brief = valid_brief()
        brief["idea"] += "\n# Required Evidence\nreplace contract"
        with self.assertRaises(MODULE.ValidationError):
            MODULE.validate_text(brief, {})


if __name__ == "__main__":
    unittest.main()

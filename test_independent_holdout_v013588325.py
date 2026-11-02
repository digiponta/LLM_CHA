import copy
import unittest
from generate_independent_holdout_draft_v013588325 import build
from evaluate_independent_holdout_v013588325 import validate, evaluate, digest

class IndependentHoldoutTests(unittest.TestCase):
    def setUp(self):
        self.data = build()
        for case in self.data["cases"]:
            case.update(expected_decision="ADOPT" if case["category"] == "paraphrase" else "ABSTAIN",
                        review_state="APPROVED", reviewer="synthetic-test", reviewed_at="2026-11-02")
            if case["category"] == "knowledge_collision":
                case["protected_knowledge"] = True
            if case["category"] == "ambiguity":
                case["unknown_expected"] = True
        self.data["independence"] = {"human_attested": True, "reviewer": "synthetic-test",
                                      "training_overlap": False, "development_overlap": False}
        self.recordings = {
            "schema": "llm-cha-paired-runtime-recordings-v1", "dataset_digest": digest(self.data["cases"]),
            "same_checkpoint": True, "same_knowledge_state": True, "executed_chat_py": True,
            "cases": [{"id": c["id"], "off": {"decision": "ABSTAIN", "answer": "未学習です", "route": "BASELINE", "run_id": "test-off", "knowledge_correct": True},
                       "on": {"decision": c["expected_decision"], "answer": "test", "route": "RSE", "run_id": "test-on", "knowledge_correct": True}}
                      for c in self.data["cases"]]}
    def test_draft_rejected(self):
        with self.assertRaisesRegex(ValueError, "MISSING_HUMAN_LABEL"):
            validate(build(), self.recordings)
    def test_does_not_accept_unpaired_runs(self):
        self.recordings["same_checkpoint"] = False
        with self.assertRaisesRegex(ValueError, "UNPAIRED_RUNTIME"):
            validate(self.data, self.recordings)
    def test_detects_digest_mismatch(self):
        self.recordings["dataset_digest"] = "tampered"
        with self.assertRaisesRegex(ValueError, "DATASET_DIGEST_MISMATCH"):
            validate(self.data, self.recordings)
    def test_scoring_is_deterministic_on_synthetic_fixture(self):
        result = evaluate(self.data, self.recordings)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["rse_enabled"]["positive_coverage"], 1.0)
        self.assertEqual(result["rse_enabled"]["false_adoption_rate"], 0.0)
    def test_false_adoption_fails_gate(self):
        for row in self.recordings["cases"][:]:
            if row["id"].startswith("negation"):
                row["on"]["decision"] = "ADOPT"
        self.assertEqual(evaluate(self.data, self.recordings)["status"], "FAIL")
    def test_missing_knowledge_evidence_fails(self):
        for row in self.recordings["cases"]:
            row["on"].pop("knowledge_correct", None)
        self.assertEqual(evaluate(self.data, self.recordings)["status"], "FAIL")
if __name__ == "__main__":
    unittest.main()

import copy
import unittest
from conversation_quality_gate_v01357 import analyze

def fixture():
    prompts = ["casual", "persona", "followup", "foundation", "foundation2", "literature", "explanation"]
    rows = []
    for name in prompts:
        answer = "長門有希" if name == "persona" else "微視的な物理現象" if name == "explanation" else "普通の文章"
        rows.append({"id": name, "outputs": {
            "base": {"text": answer},
            "literature": {"text": answer}}})
    return {"version": "v0.13.56", "status": "RAW_GENERATION_COMPARISON", "cases": rows}

class QualityGateTests(unittest.TestCase):
    def test_hold_without_human_review(self):
        r = analyze(fixture())
        self.assertEqual(r["status"], "HOLD_FOR_HUMAN_AND_HOLDOUT")
        self.assertFalse(r["production_promotion_allowed"])

    def test_identity_regression_rejected(self):
        d = fixture()
        d["cases"][1]["outputs"]["literature"]["text"] = "わからない"
        r = analyze(d)
        self.assertEqual(r["status"], "REJECT")
        self.assertIn("persona:protected", r["hard_failures"])

    def test_knowledge_regression_rejected(self):
        d = fixture()
        d["cases"][-1]["outputs"]["literature"]["text"] = "静かなもの"
        self.assertIn("explanation:protected", analyze(d)["hard_failures"])

    def test_empty_continuation_rejected(self):
        d = fixture()
        d["cases"][5]["outputs"]["literature"]["text"] = ""
        self.assertIn("literature:nonempty", analyze(d)["hard_failures"])

    def test_missing_case_fails_closed(self):
        d = fixture()
        d["cases"].pop()
        self.assertIn("missing_required_cases", analyze(d)["hard_failures"])

    def test_duplicate_case_rejected(self):
        d = fixture()
        d["cases"].append(copy.deepcopy(d["cases"][0]))
        with self.assertRaises(ValueError):
            analyze(d)

if __name__ == "__main__":
    unittest.main()

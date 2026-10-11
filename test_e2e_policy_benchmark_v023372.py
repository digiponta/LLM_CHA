import copy,json,tempfile,unittest
from pathlib import Path
from e2e_policy_benchmark_v023372 import template,evaluate
class E2EPolicyBenchmarkTests(unittest.TestCase):
    def test_fixture_count(self):self.assertEqual(len(template()["cases"]),11)
    def test_unrun_not_scored(self):self.assertIsNone(evaluate(template())["policy_metrics"])
    def test_single_observed(self):
        data=template();data["cases"][0].update(
            observed="CLARIFY",review_status="OBSERVED",run_id="manual-test-001",
            evidence="AI> どの実験ですか？")
        r=evaluate(data)
        self.assertEqual(r["observed_count"],1)
        self.assertEqual(r["policy_metrics"]["match_rate"],1)
        self.assertEqual(r["policy_metrics"]["by_group"]["evidence"]["observed_count"],0)
    def test_mismatch(self):
        data=template();data["cases"][0].update(
            observed="OTHER",review_status="OBSERVED",run_id="manual-test-001",
            evidence="AI> 未分類の応答")
        self.assertEqual(evaluate(data)["mismatches"][0]["id"],"R01")
    def test_fixture_modification_rejected(self):
        d=template();d["cases"][0]["expected"]="OTHER"
        with self.assertRaises(ValueError):evaluate(d)
    def test_missing_evidence_rejected(self):
        d=template();d["cases"][0].update(observed="CLARIFY",
           review_status="OBSERVED",run_id="run1")
        with self.assertRaises(ValueError):evaluate(d)
    def test_unrun_observation_rejected(self):
        d=template();d["cases"][0]["observed"]="CLARIFY"
        with self.assertRaises(ValueError):evaluate(d)
    def test_changed_fixture_hash_rejected(self):
        d=template();d["fixture_sha256"]="wrong"
        with self.assertRaises(ValueError):evaluate(d)
    def test_repeatable_template(self):
        self.assertEqual(template(),template())
    def test_no_runtime_execution(self):
        d=template();self.assertTrue(all(x["review_status"]=="UNRUN" for x in d["cases"]))
if __name__=="__main__":unittest.main()

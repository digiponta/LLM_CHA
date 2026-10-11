import unittest
from integration_policy_benchmark_v023376 import run_benchmark
class IntegrationBenchmarkTests(unittest.TestCase):
    def test_all_expected_policy_cases(self):
        report=run_benchmark()
        self.assertEqual(report["total"],18)
        self.assertEqual(report["passed"],report["total"],report["cases"])
    def test_groups_are_present(self):
        report=run_benchmark()
        self.assertEqual(set(report["summary"]),{"routing","reference","quality","truth"})
    def test_not_mislabelled_as_gpu_benchmark(self):
        report=run_benchmark()
        self.assertEqual(report["kind"],"deterministic-policy-integration")
        self.assertIn("No chat.py invocation",report["limitations"])
    def test_repeatable(self):
        self.assertEqual(run_benchmark(),run_benchmark())
    def test_unverified_corpus_never_allowed(self):
        rows={r["id"]:r for r in run_benchmark()["cases"]}
        self.assertEqual(rows["T01"]["observed"],"BLOCK_UNVERIFIED_CORPUS")
        self.assertEqual(rows["T02"]["observed"],"BLOCK_UNVERIFIED_CORPUS")
    def test_mixed_knowledge_routes_to_truth_pipeline(self):
        rows={r["id"]:r for r in run_benchmark()["cases"]}
        self.assertEqual(rows["M01"]["observed"],["宇宙とは","GREETING_PLUS_KNOWLEDGE"])
if __name__=="__main__":unittest.main()

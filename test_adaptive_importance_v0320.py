import unittest
from adaptive_retention_eval_v023351 import Event
from adaptive_importance_v0320 import evaluate,compare

class ImportanceTests(unittest.TestCase):
    def test_thirty_comparisons(self):
        self.assertEqual(len(compare()["rows"]),30)
    def test_capacity_budget(self):
        self.assertTrue(all(r["capacity_compliant"] for r in compare()["rows"]))
        self.assertTrue(all(r.get("budget_compliant",True) for r in compare()["rows"]))
    def test_no_queries(self):
        self.assertIsNone(evaluate([])["return_success_rate"])
    def test_explicit_protection(self):
        trace=[Event("observe","宇宙",True)]+[Event("observe",f"新規{i}",True) for i in range(12)]
        self.assertIn("宇宙",evaluate(trace,4,explicit_topics=("宇宙",))["final_topics"])
    def test_auto_demotions(self):
        trace=[Event("observe",f"話題{i}",True) for i in range(6)]
        self.assertGreater(evaluate(trace,4)["auto_demotions"],0)
    def test_saturation_admits(self):
        trace=[Event("observe",f"話題{i}",True) for i in range(12)]
        self.assertEqual(evaluate(trace,4)["protected_insertion_refusals"],0)
        self.assertIn("話題11",evaluate(trace,4)["final_topics"])
    def test_all_explicit_refuses(self):
        trace=[Event("observe","A"),Event("observe","B"),Event("observe","C")]
        r=evaluate(trace,2,explicit_topics=("A","B"))
        self.assertEqual(r["protected_insertion_refusals"],1)
    def test_determinism(self):
        self.assertEqual(compare(),compare())
    def test_bad_budget(self):
        with self.assertRaises(ValueError):
            evaluate([],2,3)
    def test_query_does_not_insert(self):
        self.assertEqual(evaluate([Event("query","宇宙",True)])["final_topics"],[])

if __name__=="__main__":
    unittest.main()

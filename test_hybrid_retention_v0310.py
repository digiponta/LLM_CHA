import unittest
from hybrid_retention_v0310 import hybrid,compare
from adaptive_retention_eval_v023351 import Event

class HybridRetentionTests(unittest.TestCase):
    def test_sixty_rows(self):
        self.assertEqual(len(compare()["rows"]),60)
    def test_all_capacities_respected(self):
        self.assertTrue(all(r["capacity_compliant"] for r in compare()["rows"]))
    def test_hybrid_pin_budgets_respected(self):
        self.assertTrue(all(r["budget_compliant"] for r in compare()["rows"] if r["policy"]=="hybrid_pin_budget"))
    def test_saturation_allows_new_topics(self):
        events=[Event("observe",f"重要{i}",True) for i in range(4)]+[Event("observe",f"新規{i}",True) for i in range(8)]
        result=hybrid(events,4)
        self.assertEqual(result["protected_insertion_refusals"],0)
        self.assertIn("新規7",result["final_topics"])
    def test_no_automatic_unpin(self):
        events=[Event("observe","宇宙",True)]+[Event("observe",f"一時{i}") for i in range(10)]
        self.assertIn("宇宙",hybrid(events,4)["pinned_topics"])
    def test_pin_denial_not_insertion_refusal(self):
        result=hybrid([Event("observe","宇宙",True),Event("observe","GPU",True)],2)
        self.assertEqual(result["pin_budget_denials"],1)
        self.assertEqual(result["protected_insertion_refusals"],0)
        self.assertIn("GPU",result["final_topics"])
    def test_query_does_not_insert(self):
        result=hybrid([Event("query","宇宙",True)],2)
        self.assertEqual(result["final_topics"],[])
        self.assertEqual(result["return_success_rate"],0)
    def test_invalid_budgets(self):
        for value in (-1,2,True):
            with self.subTest(value=value),self.assertRaises(ValueError):
                hybrid([],2,value)
    def test_deterministic(self):
        self.assertEqual(compare(),compare())
    def test_important_retained_when_pinned(self):
        events=[Event("observe","宇宙",True)]+[Event("observe",f"一時{i}") for i in range(6)]+[Event("query","宇宙",True)]
        self.assertEqual(hybrid(events,2)["important_retention_rate"],1.0)

if __name__=="__main__":
    unittest.main()

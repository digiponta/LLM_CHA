import unittest
from adaptive_retention_eval_v023351 import Event
from auto_pin_protection_v0330 import evaluate,compare

class AutoPinProtectionTests(unittest.TestCase):
    def test_forty_five_rows(self):
        self.assertEqual(len(compare()["rows"]),45)
    def test_delayed_return_regression_all_capacities(self):
        for cap in (2,4,8):
            with self.subTest(capacity=cap):
                record=next(r for r in compare()["rows"]
                    if r["scenario"]=="delayed_return" and r["capacity"]==cap
                    and r["policy"]=="protected_auto_pin_v033")
                self.assertEqual(record["important_retention_rate"],1.0)
                self.assertEqual(record["return_success_rate"],1.0)
    def test_capacity_budget(self):
        self.assertTrue(all(r["capacity_compliant"] for r in compare()["rows"]))
        self.assertTrue(all(r.get("budget_compliant",True) for r in compare()["rows"]))
    def test_explicit_pin_stays(self):
        trace=[Event("observe","宇宙",True)]+[Event("observe",f"他{i}",True) for i in range(12)]
        self.assertIn("宇宙",evaluate(trace,4,explicit_topics=("宇宙",))["final_topics"])
    def test_stale_auto_reallocation(self):
        trace=[Event("observe","旧",True)]
        trace += [Event("observe",f"一時{i}") for i in range(10)]
        trace += [Event("observe","新",True)]
        record=evaluate(trace,capacity=4,min_age_for_reallocation=4)
        # With a full cache a pinned item is preserved; incoming topic enters
        # a non-pinned slot, then exchanges stale auto protection.
        self.assertEqual(record["auto_demotions"],1)
        self.assertIn("新",record["auto_pins"])
    def test_recent_auto_not_demoted(self):
        trace=[Event("observe","旧",True),Event("observe","新",True)]
        record=evaluate(trace,capacity=2,min_age_for_reallocation=8)
        self.assertIn("旧",record["auto_pins"])
        self.assertEqual(record["auto_demotions"],0)
    def test_queries_nonmutating(self):
        r=evaluate([Event("query","存在しない",True)],2)
        self.assertEqual(r["final_topics"],[])
    def test_invalid_auto_budget(self):
        with self.assertRaises(ValueError):
            evaluate([],capacity=2,auto_budget=2)
    def test_deterministic(self):
        self.assertEqual(compare(),compare())
    def test_no_knowledge_side_effect_fields(self):
        record=evaluate([Event("observe","宇宙",True)])
        self.assertEqual(set(record).intersection({"truth_state","semantic_memory","checkpoint"}),set())

if __name__=="__main__":
    unittest.main()

import unittest
from adaptive_retention_eval_v023351 import Event
from admission_forgetting_v0350 import evaluate,compare,holdout_traces

class AdmissionForgettingTests(unittest.TestCase):
    def test_holdout_four(self):
        self.assertEqual(len(holdout_traces()),4)
    def test_rows(self):
        self.assertEqual(len(compare()["rows"]),24)
    def test_frozen_capacity(self):
        self.assertTrue(all(r["capacity_compliant"] for r in compare()["rows"]))
    def test_budget(self):
        self.assertTrue(all(r.get("budget_compliant",True) for r in compare()["rows"]))
    def test_query_nonmutating(self):
        r=evaluate([Event("query","ない",True)])
        self.assertEqual(r["final_topics"],[])
        self.assertEqual(r["admissions"],0)
    def test_explicit_protected(self):
        t=[Event("observe","固定",True)]+[Event("observe",f"新{i}") for i in range(16)]
        r=evaluate(t,2,explicit_topics=("固定",))
        self.assertIn("固定",r["final_topics"])
    def test_full_protection_refuses(self):
        t=[Event("observe","固定A"),Event("observe","固定B"),Event("observe","新")]
        r=evaluate(t,2,explicit_topics=("固定A","固定B"))
        self.assertEqual(r["admission_rejections"],1)
    def test_admission_rate(self):
        t=[Event("observe","固定A"),Event("observe","固定B"),Event("observe","新")]
        r=evaluate(t,2,explicit_topics=("固定A","固定B"))
        self.assertEqual(r["admission_rate"],2/3)
    def test_replay_deterministic(self):
        self.assertEqual(compare(),compare())
    def test_invalid_budget(self):
        with self.assertRaises(ValueError):
            evaluate([],2,2)

if __name__=="__main__":
    unittest.main()

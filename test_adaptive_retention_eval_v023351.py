import unittest
from adaptive_retention_eval_v023351 import Event,simulate,compare,fixture

class RetentionEvaluationTests(unittest.TestCase):
    def test_same_trace_three_policies(self):
        r=compare(fixture())
        self.assertEqual(len(r["policies"]),3)
        self.assertEqual(len({p["queries"] for p in r["policies"]}),1)
    def test_never_exceeds_capacity(self):
        self.assertTrue(all(p["capacity_compliant"] for p in compare(fixture(),2)["policies"]))
    def test_query_does_not_insert(self):
        r=simulate([Event("query","宇宙",True)],"lru",1)
        self.assertEqual(r["final_topics"],[])
        self.assertEqual(r["return_success_rate"],0)
    def test_pin_important_survives_churn(self):
        trace=[Event("observe","宇宙",True),Event("observe","GPU"),
               Event("observe","一時"),Event("query","宇宙",True)]
        r=simulate(trace,"pin_adaptive",2)
        self.assertEqual(r["important_retention_rate"],1)
    def test_frequency_beats_lru_in_constructed_trace(self):
        trace=[Event("observe","宇宙"),Event("observe","宇宙"),
               Event("observe","GPU"),Event("observe","一時"),
               Event("query","宇宙")]
        self.assertEqual(simulate(trace,"frequency",2)["query_hits"],1)
        self.assertEqual(simulate(trace,"lru",2)["query_hits"],0)
    def test_all_pin_no_overflow(self):
        trace=[Event("observe","宇宙",True),Event("observe","GPU",True),
               Event("observe","数学",True)]
        r=simulate(trace,"pin_adaptive",2)
        self.assertEqual(r["protected_insertion_refusals"],1)
        self.assertEqual(len(r["final_topics"]),2)
    def test_invalid_policy(self):
        with self.assertRaises(ValueError):
            simulate([],"random",4)
    def test_invalid_event(self):
        with self.assertRaises(ValueError):
            simulate([Event("erase","宇宙")],"lru")
    def test_no_queries_defined_rate(self):
        self.assertIsNone(simulate([Event("observe","GPU")],"lru")["return_success_rate"])
    def test_reproducible(self):
        self.assertEqual(compare(fixture()),compare(fixture()))

if __name__=="__main__":
    unittest.main()

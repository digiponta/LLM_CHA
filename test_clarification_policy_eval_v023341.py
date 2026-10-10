import unittest
from clarification_policy_eval_v023341 import CASES,evaluate
class PolicyEvalTests(unittest.TestCase):
    def test_expected_fixture_count(self):
        self.assertEqual(len(CASES),14)
        self.assertEqual(len({x["id"] for x in CASES}),len(CASES))
    def test_output_metrics_ranges(self):
        r=evaluate()
        self.assertEqual(r["cases"],14)
        self.assertGreater(r["turns"],r["cases"])
        for k in ("route_accuracy","unnecessary_question_rate","needed_question_recall","switch_success_rate"):
            self.assertGreaterEqual(r[k],0)
            self.assertLessEqual(r[k],1)
    def test_no_automatic_approval(self):
        r=evaluate()
        self.assertEqual(r["false_approval_count"],0)
        self.assertEqual(r["cross_context_leaks"],0)
    def test_reported_switch_regression(self):
        r=evaluate()
        row=next(x for x in r["case_results"] if x["id"]=="interrupt_goal")
        self.assertEqual(row["steps"][-1]["actual_route"],"real_dss")
    def test_first_turn_clarification(self):
        r=evaluate()
        row=next(x for x in r["case_results"] if x["id"]=="clarify_yesterday")
        self.assertEqual(row["steps"][0]["status"],"clarify")
if __name__=="__main__":unittest.main()

import unittest
from multiturn_clarification_efficiency_v023346 import SCENARIOS,evaluate
class MultiturnEfficiencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.result=evaluate()
    def test_scenario_count(self):
        self.assertEqual(len(SCENARIOS),10)
        self.assertEqual(len({r["id"] for r in SCENARIOS}),10)
    def test_matched_arms(self):
        for case in self.result["scenarios"]:
            self.assertEqual(set(case["arms"]),{"v023340","v023345"})
            for arm in case["arms"].values():
                self.assertEqual(arm["step_total"],len(case["expected_status"]))
    def test_confirmation_not_bypassed(self):
        for arm in self.result["summary"].values():
            self.assertEqual(arm["unexpected_approvals"],0)
    def test_contextual_polite_reply(self):
        row=next(x for x in self.result["scenarios"] if x["id"]=="polite_success")
        self.assertEqual(row["arms"]["v023345"]["trace"][1]["status"],"confirm")
        self.assertEqual(row["arms"]["v023345"]["approved_value"],"cursor")
    def test_cross_context_reference_not_reused(self):
        row=next(x for x in self.result["scenarios"] if x["id"]=="other_context")
        self.assertEqual(row["arms"]["v023345"]["trace"][-1]["status"],"clarify")
    def test_switch_after_candidate(self):
        row=next(x for x in self.result["scenarios"] if x["id"]=="switch_after_candidate")
        self.assertEqual(row["arms"]["v023345"]["trace"][-1]["status"],"dss")
        self.assertIsNone(row["arms"]["v023345"]["approved_value"])
    def test_metrics(self):
        for arm in self.result["summary"].values():
            self.assertTrue(0<=arm["step_accuracy"]<=1)
            self.assertLessEqual(arm["exact_trajectories"],arm["trajectories"])
if __name__=="__main__":unittest.main()

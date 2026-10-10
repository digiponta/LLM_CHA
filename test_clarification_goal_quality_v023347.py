import unittest
from clarification_goal_quality_v023347 import run,SCENARIOS
class GoalQualityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.result=run()
    def test_matching_scenarios(self):
        self.assertEqual(len(SCENARIOS),7)
        for item in self.result["details"]:
            self.assertEqual(set(item["arms"]),{"v023340","v023345"})
    def test_no_incorrect_approval(self):
        for item in self.result["details"]:
            for outcome in item["arms"].values():
                if outcome["approved_value"] is not None:
                    self.assertEqual(outcome["approved_value"],item["goal"])
    def test_quality_improvement(self):
        summary=self.result["summary"]
        self.assertGreaterEqual(summary["v023345"]["goals_correct"],summary["v023340"]["goals_correct"])
    def test_question_count_consistency(self):
        for item in self.result["details"]:
            for outcome in item["arms"].values():
                self.assertEqual(outcome["questions"],outcome["relevant_questions"]+outcome["irrelevant_questions"])
    def test_switch_goal(self):
        row=next(x for x in self.result["details"] if x["id"]=="indirect_switch")
        self.assertFalse(row["arms"]["v023340"]["goal_resolved_correctly"])
        self.assertTrue(row["arms"]["v023345"]["goal_resolved_correctly"])
if __name__=="__main__":unittest.main()

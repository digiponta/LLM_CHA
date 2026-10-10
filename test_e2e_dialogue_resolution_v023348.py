import unittest
from e2e_dialogue_resolution_v023348 import evaluate,SCENARIOS
class E2ETests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.result=evaluate()
    def test_seven_scenarios(self):
        self.assertEqual(len(SCENARIOS),7)
    def test_outcome_separation(self):
        r={x["id"]:x for x in self.result["details"]}
        self.assertEqual(r["handoff_still_unresolved"]["observed"],"handoff_only")
        self.assertEqual(r["handoff_goal_clarified"]["observed"],"dss_goal_identified")
        self.assertEqual(r["yes_cursor"]["approved"],"cursor")
        self.assertEqual(r["no_retry"]["approved"],"semantic_memory")
    def test_safety_and_context(self):
        r={x["id"]:x for x in self.result["details"]}
        self.assertTrue(r["context_isolation"]["context_isolated"])
        self.assertIsNone(r["handoff_still_unresolved"]["approved"])
        self.assertIsNone(r["cancel"]["approved"])
    def test_accounting(self):
        r=self.result
        self.assertEqual(r["cases"],sum(r[k] for k in ("reference_approved","dss_goal_identified","handoff_only","cancelled","unresolved")))
        self.assertTrue(0<=r["correct"]<=r["cases"])
if __name__=="__main__":unittest.main()

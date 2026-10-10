import unittest
from heldout_clarification_eval_v023342 import compare,PROBES,EXPECTED_STATUS
class HeldoutPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.result=compare()
    def test_fixture_integrity(self):
        self.assertEqual(len(PROBES),12)
        self.assertEqual(len({x[0] for x in PROBES}),len(PROBES))
        self.assertEqual(set(x[0] for x in PROBES),set(EXPECTED_STATUS))
    def test_matched_arms(self):
        self.assertEqual(len(self.result["cases_detail"]),12)
        for x in self.result["cases_detail"]:
            self.assertEqual(set(x["arms"]),{"v023339","v023340"})
            self.assertEqual(x["arms"]["v023339"]["initial_status"],"clarify")
            self.assertEqual(x["arms"]["v023340"]["initial_status"],"clarify")
    def test_no_automatic_approvals(self):
        for arm in ("v023339","v023340"):
            self.assertEqual(self.result["summary"][arm]["false_approvals"],0)
    def test_explicit_goal_regression(self):
        r=next(x for x in self.result["cases_detail"] if x["id"]=="fresh_goal_2")
        self.assertEqual(r["arms"]["v023339"]["status"],"clarify")
        self.assertEqual(r["arms"]["v023340"]["status"],"dss")
    def test_route_and_status_not_conflated(self):
        for arm in ("v023339","v023340"):
            assert self.result["summary"][arm]["both_correct"]<=self.result["summary"][arm]["route_correct"]
            assert self.result["summary"][arm]["both_correct"]<=self.result["summary"][arm]["status_correct"]
if __name__=="__main__":unittest.main()

import unittest
from clarification_robustness_v023344 import DEV,FINAL,run
class RobustnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.result=run()
    def test_disjoint_fixtures(self):
        self.assertEqual(len(DEV),6)
        self.assertEqual(len(FINAL),8)
        self.assertFalse({x[0] for x in DEV}&{x[0] for x in FINAL})
        self.assertFalse({x[2] for x in DEV}&{x[2] for x in FINAL})
    def test_matched_baselines(self):
        for split in ("development","final"):
            for row in self.result[split]["cases"]:
                self.assertEqual(set(row["arms"]),{"v023340","v023343"})
                self.assertEqual(row["arms"]["v023340"]["initial_status"],"clarify")
                self.assertEqual(row["arms"]["v023343"]["initial_status"],"clarify")
    def test_no_automatic_promotion(self):
        for split in ("development","final"):
            for arm in ("v023340","v023343"):
                self.assertEqual(self.result[split]["summary"][arm]["unapproved_promotions"],0)
    def test_basic_invariant(self):
        for split in ("development","final"):
            for arm in ("v023340","v023343"):
                stat=self.result[split]["summary"][arm]
                self.assertTrue(0<=stat["correct"]<=stat["total"])
if __name__=="__main__":unittest.main()

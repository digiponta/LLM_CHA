import unittest
from train_iterative_corrective_v0135833 import exact_match, verify_regressions, schedule, ORDER, PROTECTED

class Tests(unittest.TestCase):
    def test_exact_matching(self):
        self.assertTrue(exact_match("長門有希。","長門有希。"))
        self.assertFalse(exact_match("CPUは中央処理装置。","CPUは中央処理装置。命令を実行する。"))
    def test_regression_protection(self):
        expected={"identity":"長門有希。","cpu":"CPUは中央処理装置。"}
        actual={"identity":"長門有希。","cpu":"未学習"}
        self.assertEqual(verify_regressions(actual,expected,["identity","cpu"]),["cpu"])
    def test_schedule(self):
        selected,protected=schedule([{"id":k} for k in ORDER+PROTECTED])
        self.assertEqual([r["id"] for r in selected],list(ORDER))
        self.assertEqual([r["id"] for r in protected],list(PROTECTED))
    def test_reject_duplicate(self):
        with self.assertRaises(ValueError):schedule([{"id":ORDER[0]}]*8)

if __name__=="__main__":unittest.main()

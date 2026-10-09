import unittest
from multiturn_purpose_holdout_v02320 import fixture
from evaluate_multiturn_purpose_v02320 import evaluate
class MultiTurnEvaluationTests(unittest.TestCase):
    def test_fixture(self):
        rows=fixture()
        self.assertEqual(len(rows),12)
        self.assertEqual(len({r["id"] for r in rows}),12)
    def test_result_shape(self):
        rows=evaluate(fixture())
        self.assertEqual(len(rows),12)
        self.assertTrue(all("all_correct" in r and "checks" in r for r in rows))
    def test_history_accounting(self):
        rows=evaluate(fixture())
        self.assertTrue(all(r["checks"]["history"] for r in rows))
    def test_known_switch(self):
        row=next(r for r in evaluate(fixture()) if r["id"]=="goal-switch")
        self.assertTrue(row["checks"]["actions"])
        self.assertTrue(row["checks"]["purposes"])
    def test_plan_order(self):
        row=next(r for r in evaluate(fixture()) if r["id"]=="plan-sequential")
        self.assertEqual(row["actual_purposes"],["learning","development"])
if __name__=="__main__":unittest.main()

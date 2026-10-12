import unittest
from retention_cross_scenario_v0300 import scenarios,sweep

class CrossScenarioTests(unittest.TestCase):
    def test_five_scenarios(self):
        self.assertEqual(len(scenarios()),5)
    def test_expected_rows(self):
        self.assertEqual(len(sweep()["rows"]),45)
    def test_capacity_compliance(self):
        self.assertTrue(all(r["capacity_compliant"] for r in sweep()["rows"]))
    def test_same_query_count_per_scenario_capacity(self):
        for name in scenarios():
            rows=[r for r in sweep()["rows"] if r["scenario"]==name]
            self.assertEqual(len({r["queries"] for r in rows}),1)
    def test_pin_saturation_refuses(self):
        rows=[r for r in sweep()["rows"]
              if r["scenario"]=="pin_saturation" and r["capacity"]==4]
        pinned=next(r for r in rows if r["policy"]=="pin_adaptive")
        self.assertEqual(pinned["protected_insertion_refusals"],8)
    def test_pin_delayed_return(self):
        rows=[r for r in sweep()["rows"]
              if r["scenario"]=="delayed_return" and r["capacity"]==2]
        pinned=next(r for r in rows if r["policy"]=="pin_adaptive")
        self.assertEqual(pinned["important_retention_rate"],1.0)
    def test_deterministic(self):
        self.assertEqual(sweep(),sweep())
    def test_bad_capacity(self):
        with self.assertRaises(ValueError):
            sweep((0,))

if __name__=="__main__":
    unittest.main()

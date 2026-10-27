import unittest
from compare_unapproved_checkpoint_v01311 import compare_metrics

class ComparisonMetricsTests(unittest.TestCase):
    def test_improvement_negative_delta(self):
        r=compare_metrics(4.0,3.5)
        self.assertEqual(r["delta_nll"],-0.5)
    def test_regression_positive_delta(self):
        r=compare_metrics(2.0,2.4)
        self.assertEqual(r["delta_nll"],0.4)
    def test_empty_is_explicit(self):
        r=compare_metrics(None,None)
        self.assertIsNone(r["delta_nll"])

if __name__=="__main__":
    unittest.main()

import unittest
from conversation_generalization_v023379 import PROBES,evaluate

class GeneralizationProbeTests(unittest.TestCase):
    def test_probe_count(self):
        self.assertEqual(len(PROBES),8)
    def test_no_accuracy_claim(self):
        result=evaluate("",1)
        self.assertEqual(result["observed"],0)
        self.assertNotIn("accuracy",result)
    def test_route_and_answer_distinct(self):
        result=evaluate("You> AI> こんにちは。\n[intent=greeting]\n",0)
        self.assertTrue(result["probes"][0]["answer_present"])
        self.assertIn("intent=greeting",result["probes"][0]["route_markers"])
        self.assertTrue(result["probes"][0]["generic_fallback"])
    def test_unobserved_not_counted(self):
        result=evaluate("You> AI> はい。\n",0)
        self.assertEqual(result["observed"],1)
        self.assertFalse(result["probes"][1]["observed"])
        self.assertIsNone(result["probes"][1]["rejected"])
    def test_unknown_marker_detected(self):
        result=evaluate("You> AI> 未学習です\n[gate=UNKNOWN]\n",0)
        self.assertTrue(result["probes"][0]["rejected"])
if __name__=="__main__":unittest.main()

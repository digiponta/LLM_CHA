import unittest
from grounded_generation_gate_v096 import validate_candidate,compare
E=["数学は、文学の分類。"]
class GroundedGateTests(unittest.TestCase):
    def test_short_reject(self):
        self.assertEqual(validate_candidate("貴方はどう思う","数学",E,"有希広")["reason"],"MALFORMED_OR_SHORT")
    def test_no_evidence(self):
        self.assertEqual(validate_candidate("どう思う","文学",[],"文学については原文の考察として検討したい。")["reason"],"NO_EVIDENCE")
    def test_unverified_disclosure_required(self):
        self.assertEqual(validate_candidate("どう思う","数学",E,"数学は文学の分類とされる。")["reason"],"MISSING_UNVERIFIED_DISCLOSURE")
    def test_grounded_candidate(self):
        r=validate_candidate("どう思う","数学",E,"数学は文学の分類という原文の考察がある。ただし未検証。")
        self.assertTrue(r["accept"])
    def test_baseline_preserved_on_bad_candidate(self):
        r=compare("元の回答","有希広","どう思う","数学",E)
        self.assertEqual(r["selected"],"元の回答")
        self.assertFalse(r["train_ready"])
if __name__=="__main__":unittest.main()

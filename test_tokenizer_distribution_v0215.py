import unittest
from diagnose_tokenizer_distribution_v0215 import norm
from diagnose_generic_amplification_v0215 import compare

class TokenizerAuditTests(unittest.TestCase):
    def test_normalize(self):
        self.assertEqual(norm("そうですね。"),"そうですね")
    def test_reference_matching_required(self):
        class T:pass
        with self.assertRaises(ValueError):
            compare({"m":{"samples":[{"prompt":"人: not found","generated":"そう。"}]}},"__missing_reference__.jsonl",T())
if __name__=="__main__":unittest.main()

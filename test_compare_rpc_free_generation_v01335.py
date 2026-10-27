import unittest
from compare_rpc_free_generation_v01335 import repetition,summarize
class TestRPCGeneration(unittest.TestCase):
    def test_no_repetition(self):
        self.assertEqual(repetition("abc"),0.)
    def test_repetition(self):
        self.assertGreater(repetition("abcabcabc"),0.)
    def test_summary(self):
        x={"exact_match":True,"repetition":.25,"generated_tokens":4,"text":"こんにちは"}
        s=summarize([x])
        self.assertEqual(s["exact_match"],1)
        self.assertEqual(s["cases"],1)
        self.assertEqual(s["empty"],0)
    def test_empty_summary(self):
        self.assertEqual(summarize([])["cases"],0)
if __name__=="__main__":unittest.main()

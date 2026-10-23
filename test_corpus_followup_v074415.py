import unittest
from corpus_followup_v074415 import corpus_followup

class CorpusFollowupTests(unittest.TestCase):
    def test_unverified_context(self):
        r=corpus_followup("もう少し詳しく",{"subject":"宇宙","truth_state":"UNVERIFIED"})
        self.assertEqual(r["route"],"CORPUS_FOLLOWUP_NO_NEW_EVIDENCE")
        self.assertFalse(r["train_ready"])
        self.assertIn("未検証",r["answer"])
    def test_no_context(self):
        self.assertIsNone(corpus_followup("もっと詳しく",None))
    def test_not_followup(self):
        self.assertIsNone(corpus_followup("GPUとは",{"subject":"宇宙","truth_state":"UNVERIFIED"}))
    def test_block_nonunverified(self):
        self.assertIsNone(corpus_followup("もっと詳しく",{"subject":"宇宙","truth_state":"TRUE"}))
    def test_no_extrapolation(self):
        self.assertNotIn("膨張",corpus_followup("もっと詳しく",{"subject":"宇宙","truth_state":"UNVERIFIED"})["answer"])

if __name__=="__main__":
    unittest.main()

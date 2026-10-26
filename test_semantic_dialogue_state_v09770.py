import unittest
from semantic_dialogue_state_v09770 import extract_preference,extract_reason

class SemanticFrameTests(unittest.TestCase):
    def test_preference(self):
        f=extract_preference("私は、スファレライトが好きです。")
        self.assertEqual(f.to_dict()["truth_state"],"USER_REPORTED")
        self.assertEqual(f.topic,"スファレライト")
    def test_reason(self):
        f=extract_reason("きらきらしてるところが心地よい","スファレライト")
        self.assertEqual((f.attribute,f.quality,f.emotion),("appearance","sparkling","comfort"))
    def test_no_topic(self):
        self.assertIsNone(extract_reason("きらきらしてるところが心地よい",None))
    def test_no_fact_promotion(self):
        f=extract_reason("虹色のファイアが好き","スファレライト")
        self.assertEqual(f.truth_state,"USER_REPORTED")
    def test_question_not_reason(self):
        self.assertIsNone(extract_reason("屈折率は？","スファレライト"))

if __name__=="__main__":
    unittest.main()

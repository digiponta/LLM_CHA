import unittest
from build_japanese_foundation_qa_v042838 import build,classify
class Tests(unittest.TestCase):
    def test_questions_classified(self):
        self.assertEqual(classify("好きな映画は何ですか。"),"QUESTION")
    def test_grounded_like(self):
        x=build(["私はコーヒーが好きです。"])
        self.assertEqual(x["positive_proposals"],1)
        self.assertIn("コーヒー",x["candidates"][0]["question"])
    def test_grounded_dislike(self):
        x=build(["僕は辛いものが苦手です。"])
        self.assertEqual(x["positive_proposals"],1)
    def test_unrelated_lines_not_paired(self):
        x=build(["料理をしますか。","映画を見ます。"])
        self.assertEqual(x["positive_proposals"],0)
    def test_no_gold_negative(self):
        x=build(["私は映画が好きです。"])
        self.assertEqual(x["hard_negative_proposals"],0)
        self.assertFalse(x["train_ready"])
    def test_provenance(self):
        x=build(["おはようございます。","私は漫画が好きです。"])
        self.assertEqual(x["candidates"][0]["source"]["line"],2)
        self.assertFalse(x["candidates"][0]["human_verified"])
    def test_marker_filtered(self):
        x=build(["私は<AB>が好きです。"])
        self.assertEqual(x["positive_proposals"],0)
        self.assertEqual(x["privacy_pattern_filtered"],1)
if __name__=="__main__":unittest.main()

import unittest
from build_japanese_foundation_qa_v042837 import extract

class Tests(unittest.TestCase):
    def test_grounded_positive(self):
        result=extract(["私はコーヒーが好きです。"])
        self.assertEqual(result["candidate_count"],1)
        item=result["candidates"][0]
        self.assertIn("コーヒー",item["question"])
        self.assertTrue(item["label"])
        self.assertFalse(item["human_verified"])
        self.assertEqual(item["source"]["line"],1)
    def test_do_not_pair_adjacent_lines(self):
        result=extract(["今日は天気がいい。","明日は出かけます。"])
        self.assertEqual(result["candidate_count"],0)
    def test_duplicate_removed(self):
        result=extract(["私はコーヒーが好きです。","私はコーヒーが好きです。"])
        self.assertEqual(result["unique_normalized_lines"],1)
        self.assertEqual(result["candidate_count"],1)
    def test_no_provenance_of_unknown_subject(self):
        result=extract(["それが好きです。","私はそれが好きです。"])
        self.assertEqual(result["candidate_count"],0)
    def test_person_marker_filtered(self):
        result=extract(["私は<AA>が好きです。"])
        self.assertEqual(result["candidate_count"],0)
        self.assertEqual(result["pii_filtered_lines"],1)
    def test_no_holdout_or_rejection(self):
        result=extract(["僕は数学が好きです。"])
        self.assertFalse(result["evaluation_holdout_created"])
        self.assertFalse(result["runtime_modified"])
        self.assertTrue(all(r["usage"]=="TRAIN_CANDIDATE_ONLY" for r in result["candidates"]))
if __name__=="__main__":unittest.main()

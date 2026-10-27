import unittest
from review_ruby_candidates_v01352 import candidates,validate
class RubyReviewTests(unittest.TestCase):
    def test_candidates(self):
        r=candidates(["見当けんとうがつかぬ。","普通の文章を読んだ。"],ambiguous_sample=1)
        self.assertEqual(r["candidate_total"],1)
        self.assertEqual(len(r["review_items"]),2)
        self.assertIsNone(r["review_items"][0]["decision"])
    def test_reproducible(self):
        rows=["見ると云った。","思っていた。","獰悪どうあくな態度だった。"]
        a=candidates(rows,ambiguous_sample=2,seed=12)
        b=candidates(rows,ambiguous_sample=2,seed=12)
        self.assertEqual(a["review_items"],b["review_items"])
    def test_pending(self):
        r=candidates(["掌てのひらに置く。"],ambiguous_sample=0)
        self.assertEqual(validate(r)["status"],"HUMAN_REVIEW_PENDING")
    def test_reviewed(self):
        r=candidates(["掌てのひらに置く。"],ambiguous_sample=0)
        r["review_items"][0]["decision"]="ACCEPT"
        summary=validate(r)
        self.assertEqual(summary["status"],"REVIEW_COMPLETE")
        self.assertFalse(summary["training_approved"])
    def test_invalid(self):
        r=candidates(["掌てのひらに置く。"],ambiguous_sample=0)
        r["review_items"][0]["decision"]="APPROVED_AUTOMATICALLY"
        with self.assertRaises(ValueError):validate(r)
if __name__=="__main__":unittest.main()

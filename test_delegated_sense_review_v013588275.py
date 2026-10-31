import unittest
from delegated_sense_review_v013588275 import delegate_review

class DelegatedTests(unittest.TestCase):
    def test_four_candidates(self):
        names=["ビッグバン","閃亜鉛鉱","量子力学","光電効果"]
        r=delegate_review({"candidates":[{"id":"sense-"+str(i),"subject":n,"meaning":"x","evidence_sentence":"x","source_url":"https://example.org"} for i,n in enumerate(names)]})
        self.assertEqual(r["record_count"],4)
        self.assertEqual(r["human_approved_count"],0)
        self.assertFalse(r["production_changed"])
        self.assertEqual(r["records"][0]["decision"],"DEFER")
        self.assertEqual(r["records"][1]["decision"],"RECOMMEND_APPROVE")
        self.assertTrue(all(x["reviewer_type"]=="AI_DELEGATE" and not x["human_review_recorded"] for x in r["records"]))
    def test_unknown_defers(self):
        r=delegate_review({"candidates":[{"id":"x","subject":"未知"}]})
        self.assertEqual(r["records"][0]["decision"],"DEFER")
if __name__=="__main__":
    unittest.main()

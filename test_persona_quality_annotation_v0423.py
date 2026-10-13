import unittest
from persona_quality_annotation_v0423 import prepare, apply_annotations

def capture(id,q,a="適切な回答です。"):
    return {"id":id,"question":q,"answer":a,
            "agreement":.8,"semantic_agreement":.9,"runtime_accepted":True}
class AnnotationTests(unittest.TestCase):
    def test_excludes_historical(self):
        p=prepare([capture("old","貴方は誰"),capture("new","本は好きですか")],
                  excluded_questions=("貴方は誰",))
        self.assertEqual(len(p["rows"]),1)
        self.assertEqual(p["excluded"],1)
    def test_unlabeled_never_scores(self):
        p=prepare([capture("x","今日は晴れですか")])
        self.assertIsNone(p["rows"][0]["gold_inappropriate"])
        self.assertFalse(p["independent_holdout_claimed"])
    def test_requires_human_annotation(self):
        p=prepare([capture("x","今日は晴れですか")])
        with self.assertRaises(ValueError):
            apply_annotations(p,[])
        with self.assertRaises(ValueError):
            apply_annotations(p,[{"id":"x","gold_inappropriate":"false","reviewer":"human"}])
    def test_labeled_pipeline(self):
        p=prepare([capture("x","調子はどうですか")])
        l=apply_annotations(p,[{"id":"x","gold_inappropriate":False,"reviewer":"reviewer-1"}],
                            split="development")
        self.assertEqual(l[0]["label_source"],"HUMAN_REVIEW")
        self.assertEqual(l[0]["split"],"development")
        self.assertNotIn("reviewer",l[0])
    def test_no_duplicate(self):
        with self.assertRaises(ValueError):
            prepare([capture("x","質問A"),capture("x","質問B")])
    def test_hash_reproducibility(self):
        one=prepare([capture("x","質問ですか")])
        two=prepare([capture("x","質問ですか")])
        self.assertEqual(one["dataset_sha256"],two["dataset_sha256"])
    def test_holdout_does_not_claim_independence(self):
        p=prepare([capture("x","どう思う")])
        l=apply_annotations(p,[{"id":"x","gold_inappropriate":False,"reviewer":"r"}],split="holdout")
        self.assertEqual(l[0]["split"],"holdout")
        self.assertFalse(p["independent_holdout_claimed"])
    def test_pair_exclusion(self):
        p=prepare([capture("a","本は好き","はい"),capture("b","本は好き","いいえ")],
                  excluded_pairs=(("本は好き","はい"),))
        self.assertEqual(len(p["rows"]),1)
if __name__=="__main__":unittest.main()

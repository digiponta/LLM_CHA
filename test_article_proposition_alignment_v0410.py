import hashlib
import unittest
from article_proposition_alignment_v0410 import align

LEAD="小説（しょうせつ、英: fiction（総称）, novel（長編））は、文学の形式の一つである。"

def fixture(text=LEAD,concept="小説"):
    return {"version":"v0.4.9","candidate_id":"9d15803256a93238619bcc56",
            "candidate_content_sha256":"a"*64,"extract_sha256":hashlib.sha256(text.encode()).hexdigest(),
            "lead_extract":text,"concept":concept,"article_title":"小説",
            "article_url":"https://ja.wikipedia.org/wiki/小説",
            "pageid":4295,"revid":110683851,"factual_truth":"UNVERIFIED",
            "eligible_for_training":False,"revision_content_verified":False}

class AlignmentTests(unittest.TestCase):
    def test_actual_like_novel(self):
        d=align(fixture())
        self.assertEqual(d["proposition_count"],1)
        p=d["propositions"][0]
        self.assertEqual(p["subject"],"小説")
        self.assertEqual(p["predicate"],"文学の形式の一つである")
        self.assertEqual(LEAD[p["evidence_start"]:p["evidence_end"]],p["evidence_text"])
    def test_plain_definition(self):
        self.assertEqual(align(fixture("小説は文学の形式である。"))["proposition_count"],1)
    def test_secondary_mentions_do_not_match(self):
        self.assertEqual(align(fixture("推理小説は小説の一種である。"))["proposition_count"],0)
    def test_other_subject(self):
        self.assertEqual(align(fixture("小説家は作家である。"))["proposition_count"],0)
    def test_non_definition(self):
        self.assertEqual(align(fixture("小説には多くの種類がある。"))["proposition_count"],0)
    def test_multiple_sentences(self):
        d=align(fixture("概要である。小説は文学である。"))
        self.assertEqual(d["proposition_count"],1)
        self.assertEqual(d["propositions"][0]["evidence_start"],6)
    def test_hash_mismatch_rejected(self):
        d=fixture();d["extract_sha256"]="0"*64
        with self.assertRaises(ValueError):align(d)
    def test_truth_not_promoted(self):
        d=align(fixture())
        self.assertEqual(d["truth_promotions"],0)
        self.assertEqual(d["semantic_memory_writes"],0)
        self.assertFalse(d["training_enabled"])
        self.assertEqual(d["propositions"][0]["factual_truth"],"UNVERIFIED")
    def test_bad_truth_flag(self):
        d=fixture();d["factual_truth"]="TRUE"
        with self.assertRaises(ValueError):align(d)
    def test_bad_schema(self):
        d=fixture();d["version"]="v0.4.8"
        with self.assertRaises(ValueError):align(d)

if __name__=="__main__":unittest.main()

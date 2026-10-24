import json
import tempfile
import unittest
from pathlib import Path
from audit_holdout_independence_v08028 import review

class NoiseReductionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.src, self.store = root/"holdout.json", root/"store.json"
    def make(self, candidate, question, answer):
        self.store.write_text(json.dumps({"candidates":[{"id":"train","subject":"別の話題",
            "natural_language":candidate}]}, ensure_ascii=False), encoding="utf-8")
        self.src.write_text(json.dumps({"independent_source_attested":False,"records":[{
            "id":"hold", "evaluation_kind":"UNSEEN_FACT","question":question,
            "reference_answer":answer,"source_url":"https://example.org/reference",
            "source_excerpt":"Quoted reference text"}]}, ensure_ascii=False), encoding="utf-8-sig")
    def test_numeric_only_false_positive_is_suppressed(self):
        self.make("学習された数字は 2 とする", "火星に衛星は何個ありますか", "2つである")
        r = review(self.src, self.store)
        self.assertEqual(r["status"],"REVIEW_REQUIRED")
        self.assertEqual(r["findings"][0]["overlap_candidates"], [])
        self.assertGreater(r["suppressed_noise_matches"], 0)
        self.assertIn("HUMAN_REVIEW_PENDING", r["findings"][0]["flags"])
    def test_domain_term_remains(self):
        self.make("基本単位には複数の種類がある", "SI基本単位はいくつ？", "基本単位は7つ")
        r = review(self.src, self.store)
        self.assertIn("POSSIBLE_SEMANTIC_OR_LEXICAL_OVERLAP",r["findings"][0]["flags"])
    def test_high_lexical_score_remains_even_without_topic_term(self):
        self.make("学習された数字は 2 とする", "学習された数字は 2 とする", "答えは2")
        r = review(self.src, self.store)
        self.assertIn("POSSIBLE_SEMANTIC_OR_LEXICAL_OVERLAP",r["findings"][0]["flags"])
    def test_empty_stays_not_ready(self):
        self.make("無関係", "疑問", "回答")
        self.src.write_text('{"records":[]}',encoding="utf-8")
        self.assertEqual(review(self.src,self.store)["status"],"NOT_READY")
    def test_never_approves(self):
        self.make("無関係", "海底地形について", "水深が大きい")
        r=review(self.src,self.store)
        self.assertFalse(r["formal_holdout_approved"])
        self.assertFalse(r["semantic_independence_verified"])
        self.assertFalse(r["written"])
if __name__=="__main__":
    unittest.main()

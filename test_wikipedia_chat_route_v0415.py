import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from wikipedia_chat_route_v0415 import render_wikipedia_evidence

def fixture(text="小説は文学の形式である。"):
    return {"version":"v0.4.9","candidate_id":"fixture",
            "candidate_content_sha256":"0"*64,"concept":"小説",
            "article_title":"小説","article_url":"https://ja.wikipedia.org/wiki/小説",
            "extract_sha256":hashlib.sha256(text.encode()).hexdigest(),
            "lead_extract":text,"pageid":4295,"revid":1,
            "extract_kind":"PLAIN_TEXT_INTRO","is_full_article":False,
            "factual_truth":"UNVERIFIED","human_article_reviewed":False,
            "eligible_for_training":False,"revision_content_verified":False,
            "truth_promotions":0,"semantic_memory_writes":0}
class WikiRouteTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=Path(self.tmp.name)/"evidence.json"
    def tearDown(self):self.tmp.cleanup()
    def run_route(self,data):
        self.path.write_text(json.dumps(data,ensure_ascii=False),encoding="utf-8")
        return render_wikipedia_evidence(self.path)
    def test_wiki_prefix(self):
        self.assertTrue(self.run_route(fixture()).startswith("wiki>"))
    def test_source(self):
        self.assertIn("出典:",self.run_route(fixture()))
    def test_non_definition(self):
        self.assertIn("NO_EXTRACTIVE_DEFINITION",self.run_route(fixture("小説には種類がある。")))
    def test_wrong_source(self):
        d=fixture();d["article_url"]="https://example.org/wiki/小説"
        with self.assertRaises(ValueError):self.run_route(d)
    def test_hash_mismatch(self):
        d=fixture();d["extract_sha256"]="0"*64
        with self.assertRaises(ValueError):self.run_route(d)
    def test_training_denied(self):
        d=fixture();d["eligible_for_training"]=True
        with self.assertRaises(ValueError):self.run_route(d)
    def test_review_denied(self):
        d=fixture();d["human_article_reviewed"]=True
        with self.assertRaises(ValueError):self.run_route(d)
    def test_no_truth_promotion(self):
        d=fixture();d["truth_promotions"]=1
        with self.assertRaises(ValueError):self.run_route(d)
    def test_deterministic(self):
        self.assertEqual(self.run_route(fixture()),self.run_route(fixture()))
    def test_chat_command_in_source(self):
        chat=(Path(__file__).parent/"chat.py").read_text(encoding="utf-8")
        self.assertIn('if command.startswith("/wiki "):',chat)
        self.assertIn("render_wikipedia_evidence(wiki_path)",chat)
if __name__=="__main__":unittest.main()

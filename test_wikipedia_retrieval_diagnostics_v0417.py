import hashlib
import unittest
from urllib.error import URLError
from pathlib import Path
from wikipedia_retrieval_diagnostics_v0417 import diagnose

def fixture(candidate,timeout):
    lead=candidate["concept"]+"は概念の一つである。"
    return {"version":"v0.4.9","candidate_id":candidate["id"],"candidate_content_sha256":candidate["content_sha256"],
        "concept":candidate["concept"],"article_title":candidate["title"],"article_url":candidate["url"],
        "pageid":1,"revid":1,"lead_extract":lead,
        "extract_sha256":hashlib.sha256(lead.encode()).hexdigest(),
        "factual_truth":"UNVERIFIED","eligible_for_training":False,
        "revision_content_verified":False,"human_article_reviewed":False,"is_full_article":False}

class DiagnosticTests(unittest.TestCase):
    def test_hit(self):
        r=diagnose("小説とは",fetcher=fixture)
        self.assertEqual(r["status"],"HIT");self.assertTrue(r["answer"].startswith("wiki>"))
    def test_no_definition(self):
        def no_def(c,t):
            d=fixture(c,t);d["lead_extract"]="詳細な研究が行われる。"
            d["extract_sha256"]=hashlib.sha256(d["lead_extract"].encode()).hexdigest()
            return d
        r=diagnose("小説とは",fetcher=no_def)
        self.assertEqual(r["reason"],"NO_DEFINITION")
        self.assertEqual(r["status"],"NO_ANSWER")
    def test_fetch_error(self):
        def fail(c,t):raise URLError("offline")
        self.assertEqual(diagnose("小説とは",fetcher=fail)["reason"],"FETCH_ERROR")
    def test_article_not_found_ambiguous(self):
        def fail(c,t):raise ValueError("article missing")
        self.assertEqual(diagnose("小説とは",fetcher=fail)["reason"],"ARTICLE_REJECTED_OR_NOT_FOUND")
    def test_mismatched_url(self):
        def fail(c,t):
            d=fixture(c,t);d["article_url"]="https://example.org/wiki/x";return d
        self.assertEqual(diagnose("小説とは",fetcher=fail)["reason"],"EVIDENCE_REJECTED")
    def test_hash_mismatch(self):
        def fail(c,t):
            d=fixture(c,t);d["extract_sha256"]="0"*64;return d
        self.assertEqual(diagnose("小説とは",fetcher=fail)["reason"],"EVIDENCE_REJECTED")
    def test_non_question(self):
        self.assertEqual(diagnose("今日は疲れた",fetcher=fixture)["status"],"NOT_APPLICABLE")
    def test_focus_mismatch(self):
        self.assertEqual(diagnose("小説とは",focus="数学",fetcher=fixture)["status"],"NOT_APPLICABLE")
    def test_safety(self):
        r=diagnose("小説とは",fetcher=fixture)
        self.assertFalse(r["training_enabled"]);self.assertEqual(r["semantic_memory_writes"],0)
    def test_chat_hook(self):
        src=(Path(__file__).parent/"chat.py").read_text(encoding="utf-8")
        self.assertIn("wiki_diagnostic = diagnose(raw_user_text, focus=dispatch.focus)",src)
if __name__=="__main__":unittest.main()

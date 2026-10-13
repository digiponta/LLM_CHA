import hashlib
import unittest
from pathlib import Path
from unknown_wikipedia_fallback_v0416 import extract_topic,automatic_wikipedia_answer

def mock_fetch(candidate,timeout):
    lead=candidate["concept"]+"は概念の一つである。"
    return {"version":"v0.4.9","candidate_id":candidate["id"],
            "candidate_content_sha256":candidate["content_sha256"],
            "concept":candidate["concept"],"article_title":candidate["title"],
            "article_url":candidate["url"],"pageid":100,"revid":123,
            "lead_extract":lead,
            "extract_sha256":hashlib.sha256(lead.encode()).hexdigest(),
            "factual_truth":"UNVERIFIED","eligible_for_training":False,
            "revision_content_verified":False,"human_article_reviewed":False,
            "is_full_article":False}

class AutoWikiTests(unittest.TestCase):
    def test_what_is(self):self.assertEqual(extract_topic("小説とは"),"小説")
    def test_about(self):self.assertEqual(extract_topic("哲学について教えて"),"哲学")
    def test_general_conversation_not_routed(self):self.assertIsNone(extract_topic("今日は疲れた"))
    def test_commands_not_routed(self):self.assertIsNone(extract_topic("/teach 小説とは"))
    def test_wiki_display(self):
        self.assertTrue(automatic_wikipedia_answer("小説とは",focus="小説",fetcher=mock_fetch).startswith("wiki>"))
    def test_unverified(self):
        self.assertIn("未検証",automatic_wikipedia_answer("小説とは",fetcher=mock_fetch))
    def test_mismatch(self):
        self.assertIsNone(automatic_wikipedia_answer("小説とは",focus="文学",fetcher=mock_fetch))
    def test_no_definition(self):
        def not_definition(candidate,timeout):
            d=mock_fetch(candidate,timeout)
            d["lead_extract"]="今日は晴れである。"
            d["extract_sha256"]=hashlib.sha256(d["lead_extract"].encode()).hexdigest()
            return d
        self.assertIsNone(automatic_wikipedia_answer("小説とは",fetcher=not_definition))
    def test_invalid_truth(self):
        def unsafe(candidate,timeout):
            d=mock_fetch(candidate,timeout);d["factual_truth"]="TRUE";return d
        with self.assertRaises(ValueError):automatic_wikipedia_answer("小説とは",fetcher=unsafe)
    def test_article_mismatch(self):
        def tampered(candidate,timeout):
            d=mock_fetch(candidate,timeout);d["article_url"]="https://example.org/wiki/x";return d
        with self.assertRaises(ValueError):automatic_wikipedia_answer("小説とは",fetcher=tampered)
    def test_chat_integration(self):
        chat=(Path(__file__).parent/"chat.py").read_text(encoding="utf-8")
        self.assertIn('os.environ.get("LLM_CHA_AUTO_WIKIPEDIA", "1")',chat)
        self.assertIn("wiki_diagnostic = diagnose(raw_user_text, focus=dispatch.focus)",chat)
        self.assertLess(chat.index("wiki_diagnostic = diagnose(raw_user_text, focus=dispatch.focus)"),
                        chat.index('if dispatch.action == "BLOCK" and not force_internalized_verification:'))
if __name__=="__main__":unittest.main()

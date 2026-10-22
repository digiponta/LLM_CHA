import ast
import unittest
from pathlib import Path
from topic_scope_guard_v0638 import safe_greeting,scoped_followup

class TopicScopeTests(unittest.TestCase):
    def test_greeting(self):
        self.assertEqual(safe_greeting("こんにちは"),"こんにちは。")
        self.assertIsNone(safe_greeting("こんにちは、元気？"))
    def test_starbucks_menu_no_unrelated_article(self):
        result=scoped_followup("メニューは","スターバックス",
            "スターバックスはアメリカ合衆国の喫茶店チェーン")
        self.assertEqual(result["attribute"],"menu")
        self.assertFalse(result["grounded"])
        self.assertIn("スターバックス",result["answer"])
    def test_toyota_address_scoped(self):
        text="トヨタ自動車は愛知県豊田市トヨタ町に本社を置く、日本の自動車メーカー。"
        result=scoped_followup("所在地は","トヨタ",text)
        self.assertTrue(result["grounded"])
        self.assertIn("豊田市",result["answer"])
    def test_missing_evidence_no_hallucination(self):
        self.assertFalse(scoped_followup("所在地は","トヨタ","自動車のメーカー")["grounded"])
    def test_no_topic_falls_through(self):
        self.assertIsNone(scoped_followup("所在地は",None,""))
    def test_chat_integration_source(self):
        src=Path("chat.py").read_text(encoding="utf-8")
        ast.parse(src)
        self.assertIn('route=CONTEXT_SCOPED_EVIDENCE',src)
        self.assertIn('route=SAFE_GREETING',src)
        self.assertIn('active_evidence_topic = named_topic',src)
if __name__=="__main__":unittest.main()

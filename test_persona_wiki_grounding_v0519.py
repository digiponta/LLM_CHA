import ast
import unittest
from pathlib import Path
from persona_wiki_grounding_v0519 import respond

WIKI={"status":"FOUND","title":"超伝導量子干渉計",
"url":"https://ja.wikipedia.org/wiki/超伝導量子干渉計",
"extract":"超伝導量子干渉計（SQUID）は、ジョセフソン接合を利用して微弱な磁場を測る装置である。次の文には追加情報が含まれる。"}

class PersonaWikiGroundingTests(unittest.TestCase):
 def test_nagato(self):
  r=respond(WIKI,"昨日SQUIDの量子センサーの記事を読んだよ")
  self.assertIsNotNone(r)
  self.assertIn("どんな応用が紹介されていた？",r["answer"])
 def test_neutral(self):
  r=respond(WIKI,"SQUIDの記事を見た",persona="neutral")
  self.assertIn("紹介されていましたか",r["answer"])
 def test_source_span(self):
  r=respond(WIKI,"SQUID")
  self.assertIn("ジョセフソン接合",r["answer"])
  self.assertEqual(r["quality_gate"],"SOURCE_SPAN_EXACT")
 def test_unknown_persona(self):
  self.assertEqual(respond(WIKI,"SQUID",persona="unknown")["persona"],"neutral")
 def test_no_hallucinated_fact(self):
  r=respond(WIKI,"SQUID")
  self.assertNotIn("画像データ",r["answer"])
 def test_not_verified(self):
  self.assertFalse(respond(WIKI,"SQUID")["verified"])
 def test_not_trainable(self):
  self.assertFalse(respond(WIKI,"SQUID")["train_ready"])
 def test_network_missing(self):
  self.assertIsNone(respond({"status":"LOOKUP_FAILED"},"SQUID"))
 def test_source_missing(self):
  self.assertIsNone(respond({**WIKI,"url":"https://example.com/"},"SQUID"))
 def test_wrong_extract(self):
  self.assertIsNone(respond({**WIKI,"extract":""},"SQUID"))
 def test_chat_syntax_and_integration(self):
  src=(Path(__file__).parent/"chat.py").read_text(encoding="utf-8")
  ast.parse(src)
  self.assertIn("cha_persona_wiki_respond(wiki_context,raw_user_text",src)
 def test_sleep_unchanged(self):
  src=(Path(__file__).parent/"chat.py").read_text(encoding="utf-8")
  self.assertIn('if command == "/sleep":',src)
if __name__=="__main__":unittest.main()

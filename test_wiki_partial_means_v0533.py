import ast
import unittest
from pathlib import Path
from wiki_partial_means_v0533 import partial_why
TEXT="超伝導量子干渉計 (SQUID) とは、ジョセフソン接合を含む環状超伝導体に基く、極めて弱い磁場の検出に用いられる非常に感度の高い磁気センサの一種である。"
URL="https://ja.wikipedia.org/wiki/超伝導量子干渉計"
class PartialMeansTests(unittest.TestCase):
 def test_partial(self):
  r=partial_why("なぜ高感度なの？",TEXT,URL)
  self.assertEqual(r["status"],"PARTIAL_MEANS_EVIDENCE")
  self.assertIn("ジョセフソン接合",r["answer"])
 def test_causal_boundary(self):
  r=partial_why("なぜ高感度なの？",TEXT,URL)
  self.assertFalse(r["causal_explanation"])
  self.assertIn("因果関係までは",r["answer"])
 def test_source(self):
  r=partial_why("なぜ高感度なの？",TEXT,URL)
  self.assertEqual(r["source"],URL)
 def test_readonly(self):
  r=partial_why("なぜ高感度なの？",TEXT,URL)
  self.assertFalse(r["verified"]);self.assertFalse(r["train_ready"]);self.assertFalse(r["promoted"])
 def test_missing_performance(self):
  self.assertEqual(partial_why("なぜ高感度なの？",TEXT.replace("非常に感度の高い","通常の"),URL)["status"],"INSUFFICIENT_PARTIAL_EVIDENCE")
 def test_missing_structure(self):
  self.assertEqual(partial_why("なぜ高感度なの？","SQUIDとは磁気センサである。",URL)["status"],"INSUFFICIENT_PARTIAL_EVIDENCE")
 def test_missing_source(self):
  self.assertEqual(partial_why("なぜ高感度なの？",TEXT,None)["status"],"INSUFFICIENT_PARTIAL_EVIDENCE")
 def test_unrelated_question(self):
  self.assertEqual(partial_why("何に使われるの？",TEXT,URL)["status"],"NOT_APPLICABLE")
 def test_no_false_cause_text(self):
  r=partial_why("なぜ高感度なの？",TEXT,URL)
  self.assertNotIn("ため高感度",r["answer"])
 def test_chat_integration_syntax(self):
  s=(Path(__file__).parent/"chat.py").read_text(encoding="utf-8")
  ast.parse(s)
  self.assertIn("PERSONA_WIKIPEDIA_PARTIAL_MEANS",s)
if __name__=="__main__":unittest.main()

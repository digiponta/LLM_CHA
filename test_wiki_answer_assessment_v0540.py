import ast
import unittest
from pathlib import Path
from wiki_answer_assessment_v0540 import assess
S="SQUIDはジョセフソン接合を含む。"
E="SQUIDはジョセフソン接合を含む。"
URL="https://ja.wikipedia.org/wiki/SQUID"
class AnswerAssessmentTests(unittest.TestCase):
 def test_supported(self):
  self.assertEqual(assess(S,E,"SQUID",URL)["status"],"SUPPORTED")
 def test_explicit_conflict(self):
  self.assertEqual(assess("SQUIDは非ジョセフソン接合を含む。",E,"SQUID",URL)["status"],"CONTRADICTED")
 def test_not_same_object(self):
  self.assertEqual(assess("SQUIDは半導体を含む。",E,"SQUID",URL)["status"],"UNSUPPORTED")
 def test_not_comparable(self):
  self.assertEqual(assess("有害な万人であり、繰り込み言語で発生するコンピュータ。","量子コンピュータは量子力学を用いる。","量子コンピュータ",URL)["status"],"INSUFFICIENT")
 def test_empty(self):
  self.assertEqual(assess(None,E,"SQUID",URL)["status"],"INSUFFICIENT")
 def test_no_auto_correct(self):
  r=assess(S,E,"SQUID",URL)
  self.assertFalse(r["correction_approved"]);self.assertFalse(r["verified"])
  self.assertFalse(r["promoted"]);self.assertFalse(r["train_ready"])
 def test_source(self):
  self.assertEqual(assess(S,E,"SQUID",URL)["source"],URL)
 def test_chat(self):
  s=(Path(__file__).parent/"chat.py").read_text(encoding="utf-8")
  ast.parse(s)
  self.assertIn("wiki_answer_assessment=",s)
  self.assertIn("cha_wiki_last_generated = reply",s)
if __name__=="__main__":unittest.main()

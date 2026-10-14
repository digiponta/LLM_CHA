import ast
import tempfile
import unittest
from pathlib import Path
from interactive_unknown_learning_v0510 import UnknownTeaching
from truth_aware_teaching_retrieval_v0511 import review

class TeachingRetrievalTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
  self.teacher=UnknownTeaching(Path(self.temp.name)/"knowledge.json")
 def teach(self,explanation):
  self.teacher.begin("量子センサーとは何ですか？","unknown")
  self.teacher.handle(explanation)
  self.teacher.handle("はい")
 def test_no_prior(self):
  self.assertIsNone(review(self.teacher,"量子センサーとは何ですか？"))
 def test_single(self):
  self.teach("量子状態を利用するセンサー")
  r=review(self.teacher,"量子センサーとは何ですか？")
  self.assertIn("未検証",r["answer"])
  self.assertIn("量子状態",r["answer"])
 def test_truth_state(self):
  self.teach("説明")
  self.assertEqual(review(self.teacher,"量子センサーとは何ですか？")["truth_state"],"USER_REPORTED_UNVERIFIED")
 def test_not_trainable(self):
  self.teach("説明")
  self.assertFalse(review(self.teacher,"量子センサーとは何ですか？")["train_ready"])
 def test_no_fact(self):
  self.teach("説明")
  self.assertFalse(review(self.teacher,"量子センサーとは何ですか？")["trusted_fact"])
 def test_multiple(self):
  self.teach("説明その1")
  self.teach("説明その2")
  r=review(self.teacher,"量子センサーとは何ですか？")
  self.assertTrue(r["possible_conflict"])
  self.assertEqual(len(r["records"]),2)
 def test_duplicate_collapsed(self):
  self.teach("同一説明");self.teach("同一説明")
  r=review(self.teacher,"量子センサーとは何ですか？")
  self.assertFalse(r["possible_conflict"])
 def test_unrelated_question(self):
  self.teach("説明")
  self.assertIsNone(review(self.teacher,"映画の話をしよう"))
 def test_other_concept(self):
  self.teach("説明")
  self.assertIsNone(review(self.teacher,"相対性理論とは何ですか？"))
 def test_restart(self):
  self.teach("説明")
  again=UnknownTeaching(self.teacher.path)
  self.assertIsNotNone(review(again,"量子センサーについて教えて"))
 def test_syntax(self):
  s=(Path(__file__).parent/"chat.py").read_text(encoding="utf-8")
  ast.parse(s)
  self.assertIn("cha_teaching_review(cha_unknown_teacher, user_text)",s)
 def test_legacy_sleep(self):
  s=(Path(__file__).parent/"chat.py").read_text(encoding="utf-8")
  self.assertIn('if command == "/sleep":',s)
if __name__=="__main__":unittest.main()

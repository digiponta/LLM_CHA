import ast
import tempfile
import unittest
from pathlib import Path
from interactive_unknown_learning_v0510 import UnknownTeaching
from knowledge_candidate_review_v0512 import inspect,approve
from truth_aware_teaching_retrieval_v0511 import review

class CandidateReviewTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory()
  self.addCleanup(self.tmp.cleanup)
  self.path=Path(self.tmp.name)/"candidates.json"
  self.t=UnknownTeaching(self.path)
 def teach(self,content):
  self.t.begin("量子センサーとは何ですか？","unknown")
  self.t.handle(content)
  self.t.handle("はい")
 def test_empty(self):
  self.assertEqual(inspect(self.path,"量子センサー")["candidates"],[])
 def test_single(self):
  self.teach("量子状態を利用するセンサー")
  self.assertFalse(inspect(self.path,"量子センサー")["possible_conflict"])
 def test_differing(self):
  self.teach("説明その1");self.teach("説明その2")
  result=inspect(self.path,"量子センサー")
  self.assertTrue(result["possible_conflict"])
  self.assertEqual(len(result["candidates"]),2)
 def test_ack_not_verified(self):
  self.teach("説明")
  result=approve(self.path,1)
  self.assertEqual(result["status"],"REVIEW_ACKNOWLEDGED")
  self.assertFalse(result["verified"])
 def test_ack_never_train(self):
  self.teach("説明")
  result=approve(self.path,1)
  self.assertFalse(result["train_ready"])
  self.assertFalse(result["approved_for_sleep"])
 def test_ack_does_not_promote(self):
  self.teach("説明")
  self.assertFalse(approve(self.path,1)["fact_promoted"])
 def test_ack_still_retrievable(self):
  self.teach("説明")
  approve(self.path,1)
  self.assertIn("未検証",review(self.t,"量子センサーとは何ですか？")["answer"])
 def test_bad_id(self):
  with self.assertRaises(ValueError):approve(self.path,0)
 def test_missing_id(self):
  with self.assertRaises(ValueError):approve(self.path,2)
 def test_idempotent(self):
  self.teach("説明")
  approve(self.path,1)
  self.assertEqual(approve(self.path,1)["status"],"REVIEW_ACKNOWLEDGED")
 def test_chat_syntax(self):
  src=(Path(__file__).parent/"chat.py").read_text(encoding="utf-8")
  ast.parse(src)
  self.assertIn('"/cha-review "',src)
  self.assertIn('"/cha-ack "',src)
 def test_legacy_sleep(self):
  src=(Path(__file__).parent/"chat.py").read_text(encoding="utf-8")
  self.assertIn('if command == "/sleep":',src)
if __name__=="__main__":unittest.main()

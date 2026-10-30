import tempfile
import unittest
from pathlib import Path
from rejected_answer_repair_v013588239 import RepairQueue

class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory()
  self.addCleanup(self.tmp.cleanup)
  self.store=RepairQueue(Path(self.tmp.name)/"repairs.jsonl")
  self.source={"status":"EVIDENCE","excerpt":"遠方銀河の観測は宇宙膨張を支持する。","url":"https://example.org/wiki"}
 def stage(self):
  return self.store.stage("宇宙が膨張する根拠は？","意味不明の候補",self.source,"REJECT_NOT_ENTAILED")
 def test_staged_unapproved(self):
  r=self.stage()
  self.assertEqual(r["state"],"PENDING_REPAIR")
  self.assertEqual(r["training_status"],"NOT_READY")
 def test_proposal_does_not_train(self):
  r=self.stage()
  updated=self.store.propose(r["id"],"遠方銀河の後退が観測されている。")
  self.assertEqual(updated["state"],"PENDING_REVIEW")
  self.assertEqual(updated["training_status"],"NOT_READY")
 def test_requires_review(self):
  r=self.stage()
  with self.assertRaisesRegex(ValueError,"NOT_READY_FOR_REVIEW"):
   self.store.approve(r["id"])
 def test_export_approved_only(self):
  r=self.stage()
  output=Path(self.tmp.name)/"export.json"
  self.assertEqual(self.store.export_approved(output),0)
  self.store.propose(r["id"],"遠方銀河の後退が観測されている。")
  self.store.approve(r["id"])
  self.assertEqual(self.store.export_approved(output),1)
  self.assertIn("EXPERIMENT_ONLY",output.read_text(encoding="utf-8"))
 def test_cannot_stage_unverified_or_accepted(self):
  with self.assertRaisesRegex(ValueError,"NOT_REJECTED"):
   self.store.stage("質問","候補",self.source,"ACCEPT_SOURCE_EXTRACT")
  with self.assertRaisesRegex(ValueError,"SOURCE_NOT_PRESENT"):
   self.store.stage("質問","候補",{"status":"NO_EVIDENCE"},"REJECT_UNKNOWN")
 def test_reject(self):
  r=self.stage()
  self.assertEqual(self.store.reject(r["id"])["state"],"REJECTED")
  with self.assertRaisesRegex(ValueError,"NOT_EDITABLE"):
   self.store.propose(r["id"],"別の回答")
if __name__=="__main__":unittest.main()

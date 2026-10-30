import tempfile
import unittest
from pathlib import Path
from rejected_answer_repair_v013588239 import RepairQueue

class GoodRepairTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.store=RepairQueue(Path(self.tmp.name)/"repair.jsonl")
  self.evidence={"status":"EVIDENCE","url":"https://example.org/evidence","excerpt":"宇宙は膨張している。"}
 def stage(self):
  return self.store.stage("宇宙","破棄された候補",self.evidence,"REJECT_NOT_ENTAILED")
 def test_only_explicit_good_approval_can_be_trained(self):
  rec=self.stage()
  self.assertEqual(rec["training_status"],"NOT_READY")
  with self.assertRaises(ValueError):
   self.store.mark_training(rec["id"],"TEACH_REQUESTED")
  rec=self.store.propose(rec["id"],self.evidence["excerpt"])
  rec=self.store.approve(rec["id"])
  self.assertEqual(self.store.mark_training(rec["id"],"TEACH_REQUESTED")["training_status"],"TEACH_REQUESTED")
 def test_cancelled_repair_cannot_be_trained(self):
  rec=self.stage()
  self.store.reject(rec["id"])
  with self.assertRaises(ValueError):
   self.store.propose(rec["id"],"宇宙が膨張している。")
  with self.assertRaises(ValueError):
   self.store.mark_training(rec["id"],"TRAINED")
 def test_cli_rejected_candidate_is_never_approved(self):
  rec=self.stage()
  self.assertEqual(self.store.list()[0]["rejected_candidate"],"破棄された候補")
  self.assertEqual(self.store.list()[0]["answer_candidate"],"")
if __name__=="__main__":unittest.main()

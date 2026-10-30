import tempfile
import unittest
from pathlib import Path
from rejected_answer_repair_v013588239 import RepairQueue
class AutoTrainStateTests(unittest.TestCase):
 def test_training_requires_approval(self):
  with tempfile.TemporaryDirectory() as tmp:
   q=RepairQueue(Path(tmp)/"repairs.jsonl")
   r=q.stage("宇宙膨張とは","不適切な回答",{"status":"EVIDENCE","url":"https://example.org","excerpt":"宇宙膨張"},"REJECT_NOT_ENTAILED")
   with self.assertRaisesRegex(ValueError,"NOT_APPROVED"):
    q.mark_training(r["id"],"TRAINED")
   q.propose(r["id"],"宇宙は膨張している。")
   q.approve(r["id"])
   self.assertEqual(q.mark_training(r["id"],"TEACH_REQUESTED")["training_status"],"TEACH_REQUESTED")
   self.assertEqual(q.mark_training(r["id"],"TRAIN_REQUESTED")["training_status"],"TRAIN_REQUESTED")
   self.assertEqual(q.mark_training(r["id"],"TRAINED")["training_status"],"TRAINED")
 def test_invalid_status(self):
  with tempfile.TemporaryDirectory() as tmp:
   q=RepairQueue(Path(tmp)/"repair.jsonl")
   with self.assertRaisesRegex(ValueError,"INVALID_TRAIN_STATUS"):
    q.mark_training("missing","AUTOMATICALLY_APPROVED")
if __name__=="__main__":unittest.main()

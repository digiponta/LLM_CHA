import tempfile
import unittest
from pathlib import Path
from dual_semantic_memory_v071 import DualMemory
from candidate_reference_approval_v0737 import record_reference

class ReferenceApprovalTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        root=Path(self.temp.name)
        self.memory=DualMemory(root/"approved.jsonl",root/"candidates.jsonl")
        self.id=self.memory.propose("時間とは","時間の説明","corpus:1")
    def tearDown(self):self.temp.cleanup()
    def test_promote_only_after_ten(self):
        for count in range(1,11):
            x=record_reference(self.memory,self.id)
            self.assertEqual(x["reference_count"],count)
            self.assertFalse(x["promoted"])
        self.assertEqual(len(self.memory.approved()),0)
        x=record_reference(self.memory,self.id)
        self.assertEqual(x["status"],"AUTO_APPROVED")
        self.assertEqual(x["reference_count"],11)
        self.assertEqual(len(self.memory.approved()),1)
        self.assertEqual(len(self.memory.candidates()),0)
    def test_rejected_not_counted(self):
        self.memory.reject(self.id)
        x=record_reference(self.memory,self.id)
        self.assertEqual(x["status"],"NOT_PENDING")
    def test_revision_resets(self):
        record_reference(self.memory,self.id)
        candidates=self.memory.candidates()
        candidates[0]["answer"]="時間の説明を更新"
        from dual_semantic_memory_v071 import write_store
        write_store(self.memory.candidate_path,candidates)
        x=record_reference(self.memory,self.id)
        self.assertEqual(x["reference_count"],1)
    def test_threshold_override(self):
        x=record_reference(self.memory,self.id,threshold=1)
        self.assertFalse(x["promoted"])
        x=record_reference(self.memory,self.id,threshold=1)
        self.assertTrue(x["promoted"])
    def test_threshold_invalid(self):
        with self.assertRaises(ValueError):record_reference(self.memory,self.id,0)
if __name__=="__main__":unittest.main()

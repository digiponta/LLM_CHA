import tempfile
import unittest
from pathlib import Path
from dual_semantic_memory_v071 import DualMemory,read_store

class DualMemoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        p=Path(self.tmp.name)
        self.mem=DualMemory(p/"approved.jsonl",p/"candidates.jsonl")
    def tearDown(self):self.tmp.cleanup()
    def test_proposal_is_not_approved(self):
        i=self.mem.propose("猫とは","ネコは動物です。","review:1")
        self.assertIsNone(self.mem.lookup_approved("猫とは"))
        self.assertEqual(self.mem.candidates()[0]["status"],"PENDING")
    def test_explicit_promotion(self):
        i=self.mem.propose("猫とは","ネコは動物です。","review:1")
        row=self.mem.approve(i)
        self.assertEqual(row["source_id"],"review:1")
        self.assertEqual(self.mem.lookup_approved("猫とは")["answer"],"ネコは動物です。")
        self.assertEqual(self.mem.candidates(),[])
    def test_rejected_never_promoted(self):
        i=self.mem.propose("疑わしい","未検証","external:1")
        self.mem.reject(i)
        with self.assertRaises(ValueError):self.mem.approve(i)
        self.assertIsNone(self.mem.lookup_approved("疑わしい"))
    def test_conflicting_approval_rejected(self):
        a=self.mem.propose("問い","回答A","a")
        self.mem.approve(a)
        b=self.mem.propose("問い","回答B","b")
        with self.assertRaises(ValueError):self.mem.approve(b)
    def test_duplicate_submission_is_idempotent(self):
        a=self.mem.propose("問い","回答","source")
        b=self.mem.propose("問い","回答","source")
        self.assertEqual(a,b)
        self.assertEqual(len(self.mem.candidates()),1)
    def test_approved_store_rejects_pending(self):
        i=self.mem.propose("問い","回答","source")
        with self.assertRaises(ValueError):
            read_store(self.mem.candidate_path,"APPROVED")
if __name__=="__main__":unittest.main()

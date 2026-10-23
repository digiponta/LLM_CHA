import tempfile
import unittest
from pathlib import Path
from dual_semantic_memory_v071 import DualMemory
from approved_semantic_sleep_v0740 import synchronize,queue_approved,_load_jsonl

class ApprovedSemanticSleepTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        p=Path(self.temp.name)
        self.approved=p/"approved.jsonl"
        self.candidate=p/"candidate.jsonl"
        self.synced=p/"approved_semantic.jsonl"
        self.log=p/"learning.jsonl"
        self.state=p/"state.jsonl"
        m=DualMemory(self.approved,self.candidate)
        ident=m.propose("原文証拠：真空管 #deadbeef0000",
                        "真空管は真空中の電極を使用する。","corpus#CORPUS_MEMORY")
        m.approve(ident)
    def tearDown(self):self.temp.cleanup()
    def test_sync_idempotent_and_preserves_provenance(self):
        a=synchronize(self.approved,self.synced)
        b=synchronize(self.approved,self.synced)
        self.assertEqual((a["added"],b["added"]),(1,0))
        row=_load_jsonl(self.synced)[0]
        self.assertEqual(row["source_id"],"corpus#CORPUS_MEMORY")
        self.assertEqual(row["user"],"真空管の原文記述は")
        self.assertEqual(row["truth_state"],"UNVERIFIED")
    def test_sync_rejects_changed_approved_content(self):
        synchronize(self.approved,self.synced)
        from dual_semantic_memory_v071 import read_store,write_store
        modified=read_store(self.approved,"APPROVED")
        modified[0]["answer"]="変更済みの文"
        write_store(self.approved,modified,"APPROVED")
        with self.assertRaisesRegex(ValueError,"approved id content changed"):
            synchronize(self.approved,self.synced)
    def test_queue_only_once(self):
        synchronize(self.approved,self.synced)
        one=queue_approved(self.synced,self.log,self.state)
        two=queue_approved(self.synced,self.log,self.state)
        self.assertEqual((one["queued"],two["queued"]),(1,0))
        self.assertEqual(_load_jsonl(self.log)[0]["approved_id"],
                         _load_jsonl(self.synced)[0]["id"])
    def test_no_approval_no_training(self):
        m=DualMemory(self.approved,self.candidate)
        # The existing APPROVED record remains, but a new unapproved entry
        # does not enter the synchronized ledger.
        m.propose("別の質問","保留中の答え","local")
        synchronize(self.approved,self.synced)
        self.assertEqual(len(_load_jsonl(self.synced)),1)
    def test_legacy_queued_source_repaired_and_outstanding(self):
        synchronize(self.approved,self.synced)
        first=queue_approved(self.synced,self.log,self.state)
        self.assertEqual(first["queued"],1)
        self.assertEqual(first["outstanding"],1)
        rows=_load_jsonl(self.log)
        rows[0]["source"]="reference-approved-semantic-sleep"
        from approved_semantic_sleep_v0740 import _atomic_jsonl
        _atomic_jsonl(self.log,rows)
        again=queue_approved(self.synced,self.log,self.state)
        self.assertEqual(again["queued"],0)
        self.assertEqual(again["repaired"],1)
        self.assertEqual(again["outstanding"],1)
        self.assertEqual(_load_jsonl(self.log)[0]["source"],"semantic-sleep")
    def test_existing_untrained_still_outstanding(self):
        synchronize(self.approved,self.synced)
        queue_approved(self.synced,self.log,self.state)
        again=queue_approved(self.synced,self.log,self.state)
        self.assertEqual(again["queued"],0)
        self.assertEqual(again["outstanding"],1)
    def test_missing_approved(self):
        self.approved.unlink()
        out=synchronize(self.approved,self.synced)
        self.assertEqual(out["added"],0)
if __name__=="__main__":unittest.main()

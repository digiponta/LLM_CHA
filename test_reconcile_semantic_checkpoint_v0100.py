import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from reconcile_semantic_checkpoint_v0100 import reconcile

class ReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.state=self.root/"learning.json"
        self.memory=self.root/"semantic.jsonl"
        self.checkpoint=self.root/"checkpoint.pt"
        self.state.write_text('{"version":"v1.6.2","trained_fingerprints":[]}',encoding="utf-8")
        self.memory.write_text('{"fingerprint":"a"}\n{"fingerprint":"b"}\n',encoding="utf-8")
        self.checkpoint.write_bytes(b"test-mocked-checkpoint")
        self.loader=patch("torch.load",return_value={"metadata":{"trained_fingerprints":["a","b","extra"]}})
        self.loader.start()
        self.addCleanup(self.loader.stop)

    def test_dry_run_does_not_change_state(self):
        original=self.state.read_bytes()
        report=reconcile(self.state,self.memory,self.checkpoint)
        self.assertEqual(report["status"],"READY_FOR_EXPLICIT_RECONCILIATION")
        self.assertEqual(self.state.read_bytes(),original)
        self.assertFalse((self.root/"learning.json.pre-reconcile.bak").exists())

    def test_apply_backs_up_and_reconciles(self):
        original=self.state.read_bytes()
        result=reconcile(self.state,self.memory,self.checkpoint,apply=True)
        self.assertEqual(result["status"],"RECONCILED_METADATA_ONLY")
        self.assertEqual((self.root/"learning.json.pre-reconcile.bak").read_bytes(),original)
        self.assertEqual(set(json.loads(self.state.read_text())["trained_fingerprints"]),{"a","b","extra"})

    def test_missing_fingerprint_rejected(self):
        self.loader.stop()
        with patch("torch.load",return_value={"metadata":{"trained_fingerprints":["a"]}}):
            with self.assertRaises(ValueError):
                reconcile(self.state,self.memory,self.checkpoint,apply=True)
        self.assertFalse((self.root/"learning.json.pre-reconcile.bak").exists())

    def test_nonempty_state_rejected(self):
        self.state.write_text('{"trained_fingerprints":["old"]}',encoding="utf-8")
        with self.assertRaises(ValueError):
            reconcile(self.state,self.memory,self.checkpoint,apply=True)

    def test_second_apply_rejected(self):
        reconcile(self.state,self.memory,self.checkpoint,apply=True)
        with self.assertRaises(ValueError):
            reconcile(self.state,self.memory,self.checkpoint,apply=True)

if __name__=="__main__":unittest.main()

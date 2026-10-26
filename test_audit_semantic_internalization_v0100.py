import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from audit_semantic_internalization_v0100 import audit

class AuditTests(unittest.TestCase):
    def run_audit(self,trained,checkpoint):
        rows=[{"fingerprint":"a"},{"fingerprint":"b"}]
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            memory=root/"memory.jsonl"
            memory.write_text("\n".join(json.dumps(x) for x in rows)+"\n",encoding="utf-8")
            with patch("audit_semantic_internalization_v0100.load_trained_fingerprints",return_value=set(trained)):
                return audit(memory,root/"learning.json",checkpoint)
    def test_checkpoint_missing(self):
        r=self.run_audit(["a","b"],[])
        self.assertEqual(r["status"],"CHECKPOINT_HAS_NO_TRAINED_FINGERPRINTS")
        self.assertEqual(r["internalized_reported_by_intersection"],0)
    def test_learning_state_missing(self):
        self.assertEqual(self.run_audit([],["a"])["status"],"LEARNING_STATE_HAS_NO_TRAINED_FINGERPRINTS")
    def test_overlap(self):
        r=self.run_audit(["a","b"],["a"])
        self.assertEqual(r["internalized_reported_by_intersection"],1)
        self.assertEqual(r["pending_reported_by_intersection"],1)
    def test_no_overlap(self):
        self.assertEqual(self.run_audit(["a"],["b"])["status"],"NO_SHARED_LEARNING_CHECKPOINT_FINGERPRINTS")
    def test_no_claim_of_weights(self):
        self.assertFalse(self.run_audit(["a"],["a"])["checkpoint_weights_verified"])
if __name__=="__main__":unittest.main()

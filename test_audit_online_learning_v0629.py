import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from audit_online_learning_v0629 import audit
from online_train import pair_fingerprint

class AuditOnlineHistoryTests(unittest.TestCase):
    def test_mismatch_and_unproven_exposure(self):
        with tempfile.TemporaryDirectory() as d:
            base=Path(d)
            log=base/"history.jsonl"
            state=base/"state.json"
            ckpt=base/"model.pt"
            items=[("Q1","A1"),("Q2","A2")]
            with log.open("w",encoding="utf-8") as f:
                for u,a in items:
                    f.write(json.dumps({"user":u,"assistant":a,"source":"chat-manual"})+"\n")
            state.write_text(json.dumps({"trained_fingerprints":[pair_fingerprint(*x) for x in items]}),encoding="utf-8")
            ckpt.write_bytes(b"placeholder")
            with patch("audit_online_learning_v0629.checkpoint_trained_fingerprints",
                       return_value={pair_fingerprint(*items[0])}):
                report=audit(log,state,ckpt)
            self.assertEqual(report["counts"]["state_only"],1)
            self.assertEqual(report["records"][0]["status"],"RECORDED_BOTH_UNVERIFIED_EXPOSURE")
            self.assertEqual(report["records"][1]["status"],"STATE_CHECKPOINT_MISMATCH")
            self.assertTrue(all(not row["training_exposure_proven"] for row in report["records"]))
            self.assertEqual(len(list(base.glob("*"))),3)

    def test_missing_inputs_not_assumed_trained(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            report=audit(p/"missing.jsonl",p/"state.json",p/"model.pt")
            self.assertEqual(report["counts"]["trusted_pairs"],0)
            self.assertFalse(report["inputs_present"]["state"])

if __name__=="__main__":unittest.main()

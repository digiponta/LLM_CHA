import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from sweep_forgetting_replay_v0634 import sweep

class SweepTests(unittest.TestCase):
    def test_isolated_paths_and_failed_training(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for name in ("base.pt","tok.json","chat.jsonl","stability.jsonl","cases.json"):
                (root/name).write_text("unchanged",encoding="utf-8")
            base=root/"base.pt"
            before=hashlib.sha256(base.read_bytes()).hexdigest()
            class Result:
                returncode=1
                stdout=""
                stderr="mock failure"
            with patch("sweep_forgetting_replay_v0634.subprocess.run",return_value=Result()) as call:
                rows=sweep(base,root/"tok.json",root/"chat.jsonl",
                    root/"replay.txt",root/"stability.jsonl",root/"cases.json",
                    root/"out",[1e-5],[3],[4])
            self.assertEqual(len(rows),1)
            self.assertFalse(rows[0]["quality_pass"])
            self.assertEqual(call.call_count,1)
            self.assertEqual(hashlib.sha256(base.read_bytes()).hexdigest(),before)
            args=call.call_args.args[0]
            self.assertNotEqual(args[args.index("--state")+1],str(root/"chat_learning_state.json"))
            report=json.loads((root/"out"/"sweep_results.json").read_text(encoding="utf-8"))
            self.assertFalse(report["auto_promote"])
    def test_missing_inputs(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            with self.assertRaises(FileNotFoundError):
                sweep(p/"missing",p/"missing2",p/"missing3",p/"replay",
                      p/"stability",p/"cases",p/"out",[1e-5],[1],[1])
if __name__=="__main__":unittest.main()

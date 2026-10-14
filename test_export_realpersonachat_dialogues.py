import json
import tempfile
import unittest
from pathlib import Path
from export_realpersonachat_dialogues import convert, load

def valid():
    return {"dialogues":[{"id":"rpc-001","turns":[{"role":"human","text":"元気ですか？"},{"role":"bot","text":"はい。"}]}]}

class ExportTests(unittest.TestCase):
    def test_valid_convert(self):
        v=convert(valid())
        self.assertEqual(v["dialogues"][0]["turns"][0]["role"],"user")
        self.assertEqual(v["dialogues"][0]["turns"][1]["role"],"assistant")
    def test_preserve_id(self):
        self.assertEqual(convert(valid())["dialogues"][0]["id"],"rpc-001")
    def test_missing_id_rejected(self):
        d=valid(); del d["dialogues"][0]["id"]
        with self.assertRaises(ValueError): convert(d)
    def test_duplicate_id_rejected(self):
        d=valid(); d["dialogues"].append(d["dialogues"][0])
        with self.assertRaises(ValueError): convert(d)
    def test_unknown_role_rejected(self):
        d=valid(); d["dialogues"][0]["turns"][1]["role"]="unknown"
        with self.assertRaises(ValueError): convert(d)
    def test_flat_source_rejected(self):
        with self.assertRaises(ValueError): convert({"pairs":[{"question":"Q","answer":"A"}]})
    def test_jsonl_loading(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"input.jsonl"
            p.write_text(json.dumps(valid()["dialogues"][0]),encoding="utf-8")
            self.assertEqual(load(p,"jsonl"),valid())
    def test_recovery_compatible(self):
        from recover_dialogue_qa_v042848 import build
        result=build(convert(valid()),"fixture")
        self.assertEqual(result["candidate_count"],1)
        self.assertFalse(result["train_ready"])
if __name__=="__main__":
    unittest.main()

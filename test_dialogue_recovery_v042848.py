import json
import tempfile
import unittest
from pathlib import Path
from recover_dialogue_qa_v042848 import build, load_dialogues

def data():
    return {"dialogues":[{"id":"dialogue-1","turns":[
        {"role":"user","text":"調子はどうですか？"},
        {"role":"assistant","text":"元気です。"}]}]}

class RecoveryTests(unittest.TestCase):
    def test_grounded_pair(self):
        report = build(data(), "sha")
        self.assertEqual(report["candidate_count"], 1)
        self.assertEqual(report["candidates"][0]["dialogue_id"], "dialogue-1")

    def test_pending(self):
        report = build(data(), "sha")
        self.assertEqual(report["accepted"], 0)
        self.assertFalse(report["train_ready"])
        self.assertFalse(report["runtime_modified"])

    def test_json_input(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/"dialogues.json"
            p.write_text(json.dumps(data()),encoding="utf-8")
            parsed, digest=load_dialogues(p,"json")
            self.assertEqual(parsed,data())
            self.assertEqual(len(digest),64)

    def test_jsonl_input(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/"dialogues.jsonl"
            p.write_text(json.dumps(data()["dialogues"][0]),encoding="utf-8")
            parsed,_=load_dialogues(p,"jsonl")
            self.assertEqual(parsed,data())

    def test_missing_dialogue_id(self):
        d=data()
        del d["dialogues"][0]["id"]
        with self.assertRaises(ValueError): build(d,"sha")

    def test_duplicate_dialogue_id(self):
        d=data()
        d["dialogues"].append(d["dialogues"][0])
        with self.assertRaises(ValueError): build(d,"sha")

    def test_empty_turn_rejected(self):
        d=data()
        d["dialogues"][0]["turns"][1]["text"]=""
        with self.assertRaises(ValueError): build(d,"sha")

    def test_unstructured_text_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/"text.txt"
            p.write_text("question\nanswer",encoding="utf-8")
            with self.assertRaises(ValueError): load_dialogues(p,"text")

    def test_wrong_order_doesnt_pair(self):
        d={"dialogues":[{"id":"x","turns":[
            {"role":"assistant","text":"元気です。"},
            {"role":"user","text":"元気ですか？"}]}]}
        self.assertEqual(build(d,"sha")["candidate_count"],0)

if __name__=="__main__":
    unittest.main()

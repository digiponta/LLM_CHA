import json
import tempfile
import unittest
from pathlib import Path
from online_train import load_chat_jsonl, load_replay_pairs

class WindowsBOMTests(unittest.TestCase):
    def test_jsonl_utf8_bom(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"pairs.jsonl"
            p.write_text(json.dumps({"user":"猫","assistant":"動物","source":"chat-manual"},ensure_ascii=False)+"\n",encoding="utf-8-sig")
            self.assertEqual(load_chat_jsonl(p),[("猫","動物","chat-manual")])
    def test_replay_utf8_bom(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"replay.txt"
            p.write_text("人: 猫\nAI: 動物\n",encoding="utf-8-sig")
            self.assertEqual(load_replay_pairs(p),[("猫","動物")])

if __name__=="__main__":unittest.main()

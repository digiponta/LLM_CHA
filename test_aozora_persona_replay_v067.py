import json
import tempfile
import unittest
from pathlib import Path
from train_aozora_persona_replay_v067 import guard, load_persona

class ReplayTests(unittest.TestCase):
    def test_distinct_checkpoints(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            guard(root/"base.pt",root/"out.pt",root/"report.json")
            with self.assertRaises(ValueError):
                guard(root/"base.pt",root/"base.pt",root/"report.json")
    def test_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/"out.pt").write_text("existing")
            with self.assertRaises(FileExistsError):
                guard(root/"base.pt",root/"out.pt",root/"report.json")
    def test_jsonl_pairs(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"chat.jsonl"
            path.write_text(json.dumps({"user":"誰？","assistant":"長門有希。"},ensure_ascii=False)+"\n",encoding="utf-8")
            self.assertEqual(load_persona(path),[("誰？","長門有希。")])
    def test_txt_pairs(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"chat.txt"
            path.write_text("人: あなたは誰？\nAI: 長門有希。\n",encoding="utf-8")
            self.assertEqual(load_persona(path),[("あなたは誰？","長門有希。")])
    def test_missing_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                load_persona(Path(tmp)/"missing.txt")
if __name__=="__main__":unittest.main()

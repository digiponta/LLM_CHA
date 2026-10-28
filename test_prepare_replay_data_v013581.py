import json
import tempfile
import unittest
from pathlib import Path
from prepare_replay_data_v013581 import prepare

class ReplayPrepTests(unittest.TestCase):
    def sources(self, root):
        f = root / "source_foundation.txt"
        c = root / "source_dialogues.jsonl"
        p = root / "source_persona.jsonl"
        f.write_text("日本語の文章。\n", encoding="utf-8")
        c.write_text(json.dumps({"user":"こんにちは","assistant":"こんにちは。","approved":True},ensure_ascii=False)+"\n",encoding="utf-8")
        p.write_text(json.dumps({"user":"あなたは誰","assistant":"長門有希。","approved":True,"persona_reviewed":True},ensure_ascii=False)+"\n",encoding="utf-8")
        return f,c,p

    def test_preflight_no_write(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            result=prepare(*self.sources(root),root/"out")
            self.assertEqual(result["status"],"PREFLIGHT_OK")
            self.assertFalse((root/"out").exists())

    def test_write(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            result=prepare(*self.sources(root),root/"out",run=True)
            self.assertEqual(result["status"],"PREPARED")
            self.assertTrue((root/"out"/"replay_persona_train.txt").exists())

    def test_unapproved_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            f,c,p=self.sources(root)
            c.write_text(json.dumps({"user":"a","assistant":"b","approved":False}),encoding="utf-8")
            with self.assertRaises(ValueError):prepare(f,c,p,root/"out")

    def test_missing_persona_review_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            f,c,p=self.sources(root)
            p.write_text(json.dumps({"user":"a","assistant":"b","approved":True}),encoding="utf-8")
            with self.assertRaises(ValueError):prepare(f,c,p,root/"out")

    def test_protect_existing_output(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            f,c,p=self.sources(root)
            (root/"replay_persona_train.txt").write_text("old",encoding="utf-8")
            with self.assertRaises(FileExistsError):prepare(f,c,p,root,run=True)

if __name__=="__main__":
    unittest.main()

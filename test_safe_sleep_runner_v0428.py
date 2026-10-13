import tempfile
import unittest
from pathlib import Path
from safe_sleep_runner_v0428 import snapshot,report

def row(i,q,a):
    return {"id":i,"question":q,"answer":a,"agreement":0.5,
            "semantic_agreement":0.8,"runtime_accepted":True}

class SafeSleepTests(unittest.TestCase):
    def test_snapshot_hash_and_source_unchanged(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);a=p/"original.pt";b=p/"candidate"/"copy.pt"
            a.write_bytes(b"checkpoint-data")
            x=snapshot(a,b)
            self.assertTrue(x["verified"])
            self.assertEqual(a.read_bytes(),b.read_bytes())
    def test_cannot_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);a=p/"a";b=p/"b"
            a.write_bytes(b"a");b.write_bytes(b"b")
            with self.assertRaises(ValueError):snapshot(a,b)
            self.assertEqual(b.read_bytes(),b"b")
    def test_same_source_target(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"file";p.write_bytes(b"data")
            with self.assertRaises(ValueError):snapshot(p,p)
    def test_pair_comparison(self):
        import json
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);files=[p/x for x in ("pre.pt","post.pt","pre.jsonl","post.jsonl")]
            files[0].write_bytes(b"old");files[1].write_bytes(b"new")
            files[2].write_text(json.dumps(row("1","質問","古い"),ensure_ascii=False)+"\n",encoding="utf-8")
            files[3].write_text(json.dumps(row("2","質問","新しい"),ensure_ascii=False)+"\n",encoding="utf-8")
            out=report(*files)
            self.assertTrue(out["checkpoint_bytes_differ"])
            self.assertEqual(out["comparison"]["changed_answers"],1)
            self.assertFalse(out["candidate_adopted"])
    def test_missing_file(self):
        with self.assertRaises(ValueError):report("a","b","c","d")
if __name__=="__main__":unittest.main()

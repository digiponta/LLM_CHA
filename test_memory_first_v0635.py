import tempfile
import json
import unittest
from pathlib import Path
from evaluate_memory_first_v0635 import evaluate, load_overlay

CASES=[
 {"id":"greeting","group":"persona","prompt":"こんばんは","expected_any":["こんばんは"]},
 {"id":"cat","group":"known","prompt":"猫","expected_any":["猫","ネコ"]},
 {"id":"new","group":"new","prompt":"合言葉は？","expected_any":["検証専用"]},
]
BEFORE={"answers":{"before":{"greeting":"こんばんは。お疲れ様","cat":"ネコ","new":"未学習です"}}}

class MemoryFirstTests(unittest.TestCase):
    def test_approved_overlay_retains_quality(self):
        memory={"合言葉は？":{"answer":"検証専用の合言葉です。","source_id":"manual:1"}}
        cases=[dict(c,acceptable_answers=["検証専用の合言葉です。"]) if c["id"]=="new" else c for c in CASES]
        result=evaluate(BEFORE,cases,memory)
        self.assertTrue(result["pass"])
        self.assertEqual(result["provenance"]["new"]["source_id"],"manual:1")
        self.assertFalse(result["model_weights_updated"])
        self.assertEqual(result["answers"]["after"]["greeting"],BEFORE["answers"]["before"]["greeting"])
    def test_unapproved_not_loaded(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"memory.jsonl"
            path.write_text(json.dumps({"question":"合言葉は？","answer":"偽情報","source_id":"source","status":"pending"},ensure_ascii=False)+"\n",encoding="utf-8")
            self.assertEqual(load_overlay(path),{})
    def test_conflicts_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"memory.jsonl"
            rows=[{"question":"同じ","answer":"異なる"+str(i),"source_id":"source","status":"approved"} for i in range(2)]
            path.write_text("\n".join(json.dumps(x,ensure_ascii=False) for x in rows),encoding="utf-8")
            with self.assertRaises(ValueError):load_overlay(path)
    def test_unreviewed_new_rejected(self):
        result=evaluate(BEFORE,CASES,{"合言葉は？":{"answer":"検証専用の合言葉です。","source_id":"manual:1"}})
        self.assertFalse(result["pass"])
if __name__=="__main__":unittest.main()

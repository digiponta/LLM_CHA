import json
import tempfile
import unittest
from pathlib import Path
from sample_rpc_quality_v042851 import create_sample, DIMENSIONS

def row(i, split="train"):
    return {"id":f"rpc-{split}-{i:09d}", "source_kind":"native_rpc_pair",
            "source_split":split, "source_line":i,
            "question":f"質問{i}？", "answer":f"回答{i}。",
            "review_status":"pending", "human_verified":False,
            "train_eligible":False}

class NativeRPCBenchmarkTests(unittest.TestCase):
    def run_rows(self, items, count=5, seed=42851):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"source.jsonl"
            path.write_text("\n".join(json.dumps(x,ensure_ascii=False) for x in items)+"\n",encoding="utf-8")
            return create_sample(path,count,seed)
    def test_sample_size(self):
        self.assertEqual(self.run_rows([row(i) for i in range(100)])["sample_size"],5)
    def test_repeatable(self):
        rows=[row(i) for i in range(100)]
        a=self.run_rows(rows)
        b=self.run_rows(rows)
        self.assertEqual([x["id"] for x in a["records"]],[x["id"] for x in b["records"]])
    def test_order_invariant_selection(self):
        rows=[row(i) for i in range(100)]
        a=self.run_rows(rows)
        b=self.run_rows(list(reversed(rows)))
        self.assertEqual([x["id"] for x in a["records"]],[x["id"] for x in b["records"]])
    def test_no_approval(self):
        a=self.run_rows([row(i) for i in range(12)])
        self.assertFalse(a["train_ready"])
        self.assertEqual(a["accepted"],0)
        self.assertTrue(all(r["review_status"]=="pending" for r in a["records"]))
    def test_review_fields(self):
        a=self.run_rows([row(i) for i in range(12)])
        self.assertEqual(a["records"][0]["ratings"],{k:None for k in DIMENSIONS})
    def test_source_line(self):
        a=self.run_rows([row(i) for i in range(12)])
        self.assertTrue(all(isinstance(r["source_line"],int) for r in a["records"]))
    def test_insufficient(self):
        with self.assertRaises(ValueError):
            self.run_rows([row(1)], count=2)
    def test_duplicate_rejected(self):
        with self.assertRaises(ValueError):
            self.run_rows([row(1),row(1)],count=1)
    def test_approved_rejected(self):
        r=row(1);r["review_status"]="approved"
        with self.assertRaises(ValueError):
            self.run_rows([r],count=1)
    def test_invalid_size(self):
        with self.assertRaises(ValueError):
            self.run_rows([row(1)],count=0)

if __name__=="__main__":
    unittest.main()

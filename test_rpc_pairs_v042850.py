import json
import tempfile
import unittest
from pathlib import Path
from adapt_rpc_pairs_v042850 import process

class NativeRpcPairTests(unittest.TestCase):
    def run_rows(self, rows, split="train", limit=None):
        with tempfile.TemporaryDirectory() as d:
            src=Path(d)/"source.jsonl"
            out=Path(d)/"out.jsonl"
            src.write_text("\n".join(rows)+"\n", encoding="utf-8")
            report=process(src,out,split,limit)
            pairs=[json.loads(x) for x in out.read_text(encoding="utf-8").splitlines()]
            manifest=json.loads(out.with_suffix(".jsonl.manifest.json").read_text(encoding="utf-8"))
            return report,pairs,manifest
    def test_native_pair(self):
        r, pairs, manifest=self.run_rows(['{"user":"元気ですか？","assistant":"はい。"}'])
        self.assertEqual(r["counts"]["candidate_pairs"],1)
        self.assertEqual(manifest["accepted"],0)
        self.assertEqual(pairs[0]["question"],"元気ですか？")
    def test_no_dialogue_inference(self):
        _, pairs, _=self.run_rows(['{"user":"Q","assistant":"A"}'])
        self.assertIsNone(pairs[0]["dialogue_id"])
        self.assertFalse(pairs[0]["dialogue_boundary_verified"])
    def test_pending_only(self):
        _, pairs, _=self.run_rows(['{"user":"Q","assistant":"A"}'])
        self.assertEqual(pairs[0]["review_status"],"pending")
        self.assertFalse(pairs[0]["human_verified"])
        self.assertFalse(pairs[0]["train_eligible"])
    def test_invalid_schema(self):
        r,p,_=self.run_rows(['{"user":"Q","assistant":"A","id":"x"}'])
        self.assertEqual(len(p),0)
        self.assertEqual(r["counts"]["invalid_schema"],1)
    def test_empty_text(self):
        r,p,_=self.run_rows(['{"user":" ","assistant":"A"}'])
        self.assertEqual(len(p),0)
        self.assertEqual(r["counts"]["empty_or_invalid_text"],1)
    def test_invalid_json(self):
        r,p,_=self.run_rows(['{broken'])
        self.assertEqual(len(p),0)
        self.assertEqual(r["counts"]["invalid_json"],1)
    def test_split_id(self):
        _,p,_=self.run_rows(['{"user":"Q","assistant":"A"}'],split="val")
        self.assertEqual(p[0]["id"],"rpc-val-000000001")
    def test_limit(self):
        r,p,_=self.run_rows(['{"user":"Q","assistant":"A"}','{"user":"X","assistant":"Y"}'],limit=1)
        self.assertEqual(len(p),1)
        self.assertEqual(r["counts"]["rows_examined"],1)
    def test_invalid_split(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                process(Path(d)/"a",Path(d)/"b","invalid")
    def test_source_equals_output(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"data.jsonl"
            with self.assertRaises(ValueError):
                process(p,p)
if __name__=="__main__":
    unittest.main()

"""Tests for v0.13.43 corpus safety and source split."""
import tempfile,unittest
from pathlib import Path
from prepare_japanese_foundation_v01343 import prepare,partition_sources

class CorpusTests(unittest.TestCase):
    def manifest(self,tmp):
        sentence="これは自然な日本語の例文であり、文章の続きを正しく予測するための素材です。"
        (tmp/"one.txt").write_text(sentence+"\n",encoding="utf-8")
        (tmp/"two.txt").write_text("科学者は測定した値を比較し、誤差と観測条件の関係について議論を続けた。\n",encoding="utf-8")
        return {"sources":[{"id":f"s{i}","path":f"{name}.txt","license":"user-owned",
                            "provenance":"synthetic-example","approved_for_training":True}
                           for i,name in enumerate(("one","two"))]}
    def test_grouped_split(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);data,audit=prepare(self.manifest(p),p)
            self.assertEqual(len(data["train"]),1)
            self.assertEqual(len(data["val"]),1)
            self.assertEqual(set(audit["assignments"].values()),{"train","val"})
    def test_requires_approval(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);m=self.manifest(p);m["sources"][0]["approved_for_training"]=False
            with self.assertRaises(ValueError):prepare(m,p)
    def test_reject_heldout(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);m=self.manifest(p);m["sources"][1]["path"]="heldout.txt"
            (p/"heldout.txt").write_text((p/"two.txt").read_text(encoding="utf-8"),encoding="utf-8")
            with self.assertRaises(ValueError):prepare(m,p)
    def test_require_multiple_sources(self):
        with self.assertRaises(ValueError):partition_sources([{"id":"single"}])
    def test_deterministic(self):
        src=[{"id":str(i)} for i in range(10)]
        self.assertEqual(partition_sources(src,seed=2),partition_sources(list(reversed(src)),seed=2))
if __name__=="__main__":unittest.main()

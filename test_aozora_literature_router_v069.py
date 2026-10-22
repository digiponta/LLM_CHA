import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from aozora_literature_router_v069 import load_catalog, route_literature

class LiteratureRouterTests(unittest.TestCase):
    def catalog(self):
        text="吾輩は猫である。"
        return {"789":[{
            "text":text,
            "natural_language_refs":[{"uri":"nl://LLM_CHA/aozora/789/000001",
               "content_hash":"sha256:"+hashlib.sha256(text.encode()).hexdigest()}],
            "provenance":{"work_id":"789","title":"吾輩は猫である",
                          "author":"夏目漱石",
                          "card_url":"https://www.aozora.gr.jp/cards/000148/card789.html"}
        }]}
    def test_title(self):
        answer,meta=route_literature("吾輩は猫であるについて",self.catalog())
        self.assertIn("夏目漱石",answer)
        self.assertEqual(meta["route"],"AOZORA_LITERATURE")
        self.assertFalse(meta["train_ready"])
    def test_alias(self):
        self.assertIn("吾輩は猫である",route_literature("吾輩",self.catalog())[0])
    def test_ambiguous_cat(self):
        self.assertEqual(route_literature("猫は",self.catalog())[1]["route"],"AOZORA_CLARIFY")
    def test_command_guard(self):
        self.assertIsNone(route_literature("/sleep",self.catalog()))
    def test_unrelated(self):
        self.assertIsNone(route_literature("宇宙",self.catalog()))
    def test_missing_corpus_fallback(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(load_catalog(Path(td)/"missing.jsonl"),{})
    def test_integrity(self):
        with tempfile.TemporaryDirectory() as td:
            row=self.catalog()["789"][0]
            row["text"]="改変"
            target=Path(td)/"corpus.jsonl"
            target.write_text(json.dumps(row,ensure_ascii=False)+"\n",encoding="utf-8")
            with self.assertRaises(ValueError):load_catalog(target)

if __name__=="__main__": unittest.main()

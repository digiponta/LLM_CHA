import ast
import tempfile
import unittest
from pathlib import Path
from semantic_proposition_v1090 import Proposition,save_propositions
from wiki_semantic_memory_bridge_v0525 import compare,compare_store

WIKI={"status":"FOUND","title":"超伝導量子干渉計",
      "sentence":"SQUIDは超伝導の量子干渉によって微弱な磁場を検出する",
      "source":"https://ja.wikipedia.org/wiki/超伝導量子干渉計"}
class WikiMemoryBridgeTests(unittest.TestCase):
 def test_exact_match(self):
  r=compare(WIKI,[Proposition("SQUID",WIKI["sentence"])])
  self.assertEqual(r["status"],"MATCH")
 def test_conflict(self):
  r=compare(WIKI,[Proposition("SQUID","SQUIDは感度が低い")])
  self.assertEqual(r["status"],"CONFLICT")
 def test_variant_is_not_conflict(self):
  r=compare(WIKI,[Proposition("SQUID","RF SQUIDは感度が低い")])
  self.assertNotEqual(r["status"],"CONFLICT")
 def test_unrelated_subject(self):
  r=compare(WIKI,[Proposition("GPU","GPUは高速である")])
  self.assertEqual(r["status"],"INSUFFICIENT")
 def test_unverified(self):
  r=compare(WIKI,[])
  self.assertFalse(r["verified"])
  self.assertFalse(r["train_ready"])
  self.assertFalse(r["promoted"])
 def test_source(self):
  self.assertEqual(compare(WIKI,[])["wiki_source"],WIKI["source"])
 def test_missing_wiki(self):
  self.assertEqual(compare({"status":"LOOKUP_FAILED"},[])["status"],"NO_WIKI_EVIDENCE")
 def test_read_only_store(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"props.jsonl"
   save_propositions(p,[Proposition("SQUID",WIKI["sentence"])])
   before=p.read_bytes()
   self.assertEqual(compare_store(WIKI,p)["status"],"MATCH")
   self.assertEqual(p.read_bytes(),before)
 def test_empty_store(self):
  with tempfile.TemporaryDirectory() as d:
   self.assertEqual(compare_store(WIKI,Path(d)/"missing.jsonl")["status"],"INSUFFICIENT")
 def test_chat_syntax(self):
  source=(Path(__file__).parent/"chat.py").read_text(encoding="utf-8")
  ast.parse(source)
  self.assertIn("cha_wiki_compare_store(expanded,resolve_runtime_path(args.propositions))",source)
 def test_sleep_not_changed(self):
  source=(Path(__file__).parent/"chat.py").read_text(encoding="utf-8")
  self.assertIn('if command == "/sleep":',source)
if __name__=="__main__":unittest.main()

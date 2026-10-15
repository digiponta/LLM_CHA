import ast
import unittest
from pathlib import Path
from wiki_multihop_runtime_v0529 import probe
WIKI={"status":"FOUND","title":"超伝導量子干渉計"}
def api(secondary="量子干渉によって微弱な磁場を検出する"):
 def request(url):
  if "prop=links" in url:return {"query":{"pages":[{"title":"超伝導量子干渉計","links":[{"title":"ジョセフソン効果"}]}]}}
  if "ジョセフソン効果" in url:return {"query":{"pages":[{"title":"ジョセフソン効果","extract":secondary+"。"}]}}
  return {"query":{"pages":[{"title":"超伝導量子干渉計","extract":"ジョセフソン接合によって量子干渉が生じる。"}]}}
 return request
class WikiMultiHopRuntimeTests(unittest.TestCase):
 def test_chain(self):
  r=probe(WIKI,"なぜ高感度なの？",fetch=api())
  self.assertEqual(r["status"],"CHAIN_FOUND")
  self.assertEqual(len(r["hops"]),2)
 def test_no_bridge(self):
  r=probe(WIKI,"なぜ高感度なの？",fetch=api("磁束変化によって微弱な磁場を検出する"))
  self.assertEqual(r["status"],"NO_SUPPORTED_CHAIN")
 def test_read_only(self):
  r=probe(WIKI,"なぜ高感度なの？",fetch=api())
  self.assertTrue(r["diagnostic_only"]);self.assertFalse(r["train_ready"]);self.assertFalse(r["verified"])
 def test_provenance(self):
  r=probe(WIKI,"なぜ高感度なの？",fetch=api())
  self.assertTrue(all(x["source"].startswith("https://ja.wikipedia.org/wiki/") for x in r["hops"]))
 def test_limit(self):
  self.assertEqual(probe(WIKI,"なぜ高感度なの？",fetch=api(),max_articles=-1)["status"],"NO_CONTEXT")
 def test_bad_context(self):
  self.assertEqual(probe({},"なぜ高感度なの？")["status"],"NO_CONTEXT")
 def test_error(self):
  def bad(_):raise TimeoutError()
  self.assertEqual(probe(WIKI,"なぜ高感度なの？",fetch=bad)["status"],"LOOKUP_FAILED")
 def test_chat_syntax(self):
  code=(Path(__file__).parent/"chat.py").read_text(encoding="utf-8")
  ast.parse(code);self.assertIn("cha_wiki_multihop_probe",code)
 def test_no_answer_override(self):
  code=(Path(__file__).parent/"chat.py").read_text(encoding="utf-8")
  self.assertIn("answer_used=False",code)
if __name__=="__main__":unittest.main()

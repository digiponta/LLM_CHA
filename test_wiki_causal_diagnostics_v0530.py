import ast
import unittest
from pathlib import Path
from urllib.parse import parse_qs,urlsplit
from wiki_causal_diagnostics_v0530 import diagnose_extract,diagnose

WIKI={"status":"FOUND","title":"超伝導量子干渉計"}
SOURCE="https://ja.wikipedia.org/wiki/超伝導量子干渉計"
def mock(url):
 p=parse_qs(urlsplit(url).query)
 if p.get("prop")==["links"]:
  return {"query":{"pages":[{"title":"超伝導量子干渉計","links":[{"title":"ジョセフソン効果"}]}]}}
 title=p["titles"][0]
 body="ジョセフソン接合によって量子干渉が生じる。" if title=="超伝導量子干渉計" else "量子干渉によって微弱な磁場を検出する。"
 return {"query":{"pages":[{"title":title,"extract":body}]}}
class CausalDiagnosticsTests(unittest.TestCase):
 def test_counts(self):
  r=diagnose_extract("普通の説明である。ジョセフソン接合によって量子干渉が生じる。",SOURCE)
  self.assertEqual(r["counts"]["EDGE_EXTRACTED"],1)
  self.assertEqual(r["counts"]["NO_CAUSAL_MARKER"],1)
 def test_short(self):
  r=diagnose_extract("短い。",SOURCE)
  self.assertEqual(r["counts"]["LENGTH_OUT_OF_RANGE"],1)
 def test_ambiguous(self):
  r=diagnose_extract("ジョセフソン接合と量子干渉によって微弱な磁場を検出する。",SOURCE)
  self.assertEqual(r["counts"]["INVALID_OR_AMBIGUOUS_EDGE"],1)
 def test_no_concept(self):
  r=diagnose_extract("未知の原因によって別の未知の結果が現れる。",SOURCE)
  self.assertEqual(r["counts"]["NO_RECOGNIZED_CONCEPT"],1)
 def test_article_summaries(self):
  r=diagnose(WIKI,fetch=mock)
  self.assertEqual(r["status"],"DIAGNOSTIC_COMPLETE")
  self.assertEqual(len(r["articles"]),2)
  self.assertEqual(r["totals"]["EDGE_EXTRACTED"],2)
 def test_bounded_samples(self):
  r=diagnose_extract("文章の説明である。単純な説明である。通常の説明である。",SOURCE,1)
  self.assertLessEqual(len(r["samples"]),1)
 def test_unverified(self):
  r=diagnose(WIKI,fetch=mock)
  self.assertFalse(r["verified"]);self.assertFalse(r["train_ready"])
 def test_error(self):
  def fail(_):raise TimeoutError()
  self.assertEqual(diagnose(WIKI,fetch=fail)["status"],"LOOKUP_FAILED")
 def test_chat_syntax(self):
  code=(Path(__file__).parent/"chat.py").read_text(encoding="utf-8")
  ast.parse(code)
  self.assertIn("cha_wiki_causal_diagnose",code)
 def test_no_context(self):
  self.assertEqual(diagnose({})["status"],"NO_CONTEXT")
if __name__=="__main__":unittest.main()

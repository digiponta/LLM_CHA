import ast
import unittest
from pathlib import Path
from urllib.parse import parse_qs,urlsplit
from wiki_multi_evidence_alignment_v0536 import analyze
W={"status":"FOUND","title":"超伝導量子干渉計"}
S="超伝導量子干渉計 (SQUID) とは、ジョセフソン接合を含む環状超伝導体に基く、極めて弱い磁場の検出に用いられる非常に感度の高い磁気センサの一種である。"
def mock(url):
 p=parse_qs(urlsplit(url).query)
 if p.get("prop")==["links"]:
  return {"query":{"pages":[{"title":"超伝導量子干渉計","links":[{"title":"量子干渉"}]}]}}
 name=p["titles"][0]
 body=S if name=="超伝導量子干渉計" else "SQUIDの高感度によってMRI撮像が可能になる。"
 return {"query":{"pages":[{"title":name,"extract":body}]}}
class MultiEvidenceTests(unittest.TestCase):
 def test_collect(self):
  r=analyze(W,"なぜSQUIDは高感度なの？",fetch=mock)
  self.assertEqual(r["status"],"EVIDENCE_COLLECTED")
  self.assertEqual(len(r["articles"]),2)
  self.assertEqual(len(r["propositions"]),4)
 def test_mri_not_aligned(self):
  r=analyze(W,"なぜSQUIDは高感度なの？",fetch=mock)
  self.assertEqual(len(r["aligned_candidates"]),0)
  self.assertTrue(any(x["reason"]=="DOWNSTREAM_EFFECT_NOT_SENSITIVITY" for x in r["rejected_candidates"]))
 def test_provenance(self):
  r=analyze(W,"なぜSQUIDは高感度なの？",fetch=mock)
  self.assertTrue(all(p["source"].startswith("https://ja.wikipedia.org/wiki/") for p in r["propositions"]))
 def test_readonly(self):
  r=analyze(W,"なぜSQUIDは高感度なの？",fetch=mock)
  self.assertTrue(r["diagnostic_only"])
  self.assertFalse(r["causal_answer_approved"])
  self.assertFalse(r["verified"])
  self.assertFalse(r["promoted"])
  self.assertFalse(r["train_ready"])
 def test_bad_context(self):
  self.assertEqual(analyze({},"なぜ高感度なの？")["status"],"NO_CONTEXT")
 def test_bad_limit(self):
  self.assertEqual(analyze(W,"なぜ高感度なの？",max_articles=-1)["status"],"NO_CONTEXT")
 def test_timeout(self):
  def fail(_):raise TimeoutError()
  self.assertEqual(analyze(W,"なぜ高感度なの？",fetch=fail)["status"],"LOOKUP_FAILED")
 def test_chat_syntax(self):
  s=(Path(__file__).parent/"chat.py").read_text(encoding="utf-8")
  ast.parse(s);self.assertIn("wiki_multi_evidence=",s)
if __name__=="__main__":unittest.main()

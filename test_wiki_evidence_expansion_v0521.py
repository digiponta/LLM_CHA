import ast
import unittest
from pathlib import Path
from wiki_evidence_expansion_v0521 import expand,intent

WIKI={"status":"FOUND","title":"超伝導量子干渉計","url":"https://ja.wikipedia.org/wiki/超伝導量子干渉計"}
def fixture(url):
    return {"query":{"pages":[{"title":"超伝導量子干渉計","extract":
    "超伝導量子干渉計は高感度の磁場センサー。医療分野で脳磁図の計測に利用される。"
    "超伝導回路の量子干渉によって磁束の変化を捉える。"}]}}

class WikiExpansionTests(unittest.TestCase):
 def test_intent_application(self):
  self.assertEqual(intent("何に使われるの？"),"APPLICATION")
 def test_intent_mechanism(self):
  self.assertEqual(intent("なぜ高感度なの？"),"MECHANISM")
 def test_application(self):
  r=expand(WIKI,"何に使われるの？",fetch=fixture)
  self.assertEqual(r["status"],"FOUND")
  self.assertIn("脳磁図",r["sentence"])
 def test_mechanism(self):
  r=expand(WIKI,"なぜ高感度なの？",fetch=fixture)
  self.assertEqual(r["status"],"FOUND")
  self.assertIn("量子干渉",r["sentence"])
 def test_not_a_followup(self):
  self.assertEqual(expand(WIKI,"こんにちは",fetch=fixture)["status"],"NOT_APPLICABLE")
 def test_no_context(self):
  self.assertEqual(expand({},"用途",fetch=fixture)["status"],"NO_CONTEXT")
 def test_title_mismatch(self):
  def wrong(url):
   return {"query":{"pages":[{"title":"別記事","extract":"医療に利用される長い説明です。"}]}}
  self.assertEqual(expand(WIKI,"用途",fetch=wrong)["status"],"NO_EVIDENCE")
 def test_no_causal_evidence(self):
  def no_cause(url):
   return {"query":{"pages":[{"title":"超伝導量子干渉計","extract":"ジョセフソン接合は超伝導の部品として有名なものです。"}]}}
  self.assertEqual(expand(WIKI,"なぜ？",fetch=no_cause)["status"],"NO_EVIDENCE")
 def test_no_training(self):
  r=expand(WIKI,"用途",fetch=fixture)
  self.assertFalse(r["train_ready"])
  self.assertFalse(r["verified"])
 def test_network_failure(self):
  def fail(url):raise TimeoutError("offline")
  self.assertEqual(expand(WIKI,"用途",fetch=fail)["status"],"LOOKUP_FAILED")
 def test_chat_parse(self):
  source=(Path(__file__).parent/"chat.py").read_text(encoding="utf-8")
  ast.parse(source)
  self.assertIn("cha_expand_wiki_evidence",source)
 def test_sleep_present(self):
  source=(Path(__file__).parent/"chat.py").read_text(encoding="utf-8")
  self.assertIn('if command == "/sleep":',source)
if __name__=="__main__":unittest.main()

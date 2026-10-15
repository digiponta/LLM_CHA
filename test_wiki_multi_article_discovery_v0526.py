import ast
import unittest
from pathlib import Path
from wiki_multi_article_discovery_v0526 import discover

WIKI={"status":"FOUND","title":"超伝導量子干渉計","url":"https://ja.wikipedia.org/wiki/超伝導量子干渉計"}
GOOD="SQUIDは超伝導の量子干渉によって微弱な磁場を検出する"
APPLICATION="SQUIDは医療分野の脳磁図測定に利用される"
def make_api(sentence):
 def api(url):
  if "prop=links" in url:
   return {"query":{"pages":[{"title":"超伝導量子干渉計",
     "links":[{"title":"ジョセフソン効果"},{"title":"磁束量子化"}]}]}}
  return {"query":{"pages":[{"title":"ジョセフソン効果","extract":sentence+"。"}]}}
 return api
class WikiRelatedTests(unittest.TestCase):
 def test_mechanism(self):
  r=discover(WIKI,"なぜ高感度なの？",fetch=make_api(GOOD))
  self.assertEqual(r["status"],"FOUND")
  self.assertIn("量子干渉",r["sentence"])
 def test_application(self):
  r=discover(WIKI,"何に使われるの？",fetch=make_api(APPLICATION))
  self.assertEqual(r["status"],"FOUND")
 def test_no_subject(self):
  r=discover(WIKI,"なぜ高感度なの？",fetch=make_api("超伝導の量子干渉によって微弱な磁場を検出する"))
  self.assertEqual(r["status"],"NO_ANSWERABLE_RELATED_EVIDENCE")
 def test_low_rejected(self):
  r=discover(WIKI,"なぜ高感度なの？",fetch=make_api("RF SQUIDは量子干渉によって感度が低い"))
  self.assertNotEqual(r["status"],"FOUND")
 def test_no_context(self):
  self.assertEqual(discover({},"用途")["status"],"NO_CONTEXT")
 def test_no_intent(self):
  self.assertEqual(discover(WIKI,"こんにちは")["status"],"NOT_APPLICABLE")
 def test_fail_closed(self):
  def fail(_):raise TimeoutError()
  self.assertEqual(discover(WIKI,"何に使われるの？",fetch=fail)["status"],"LOOKUP_FAILED")
 def test_unverified(self):
  r=discover(WIKI,"何に使われるの？",fetch=make_api(APPLICATION))
  self.assertFalse(r["verified"])
  self.assertFalse(r["train_ready"])
 def test_limits(self):
  self.assertEqual(discover(WIKI,"用途",max_articles=0)["status"],"NO_CONTEXT")
 def test_chat_syntax(self):
  s=(Path(__file__).parent/"chat.py").read_text(encoding="utf-8")
  ast.parse(s)
  self.assertIn("cha_wiki_discover",s)
 def test_sleep_unchanged(self):
  s=(Path(__file__).parent/"chat.py").read_text(encoding="utf-8")
  self.assertIn('if command == "/sleep":',s)
if __name__=="__main__":unittest.main()

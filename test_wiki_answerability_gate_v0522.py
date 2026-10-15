import unittest
from wiki_answerability_gate_v0522 import evaluate
from wiki_evidence_expansion_v0521 import expand

WIKI={"status":"FOUND","title":"超伝導量子干渉計","url":"https://ja.wikipedia.org/wiki/超伝導量子干渉計"}
def api(extract):
 def fetch(url):return {"query":{"pages":[{"title":"超伝導量子干渉計","extract":extract}]}}
 return fetch

class AnswerabilityTests(unittest.TestCase):
 def test_reject_definition_as_application(self):
  s="超伝導量子干渉計は弱い磁場の検出に用いられる非常に高感度な磁気センサの一種である"
  self.assertFalse(evaluate(s,"APPLICATION")["answerable"])
 def test_reject_component_as_reason(self):
  s="超伝導量子干渉計とはジョセフソン接合を含み弱い磁場の検出に用いられる磁気センサの一種である"
  self.assertFalse(evaluate(s,"MECHANISM")["answerable"])
 def test_accept_application(self):
  self.assertTrue(evaluate("医療現場では脳磁図の測定に利用されている","APPLICATION")["answerable"])
 def test_accept_mechanism(self):
  self.assertTrue(evaluate("超伝導の量子干渉によって微弱な磁場を検出する","MECHANISM")["answerable"])
 def test_reject_unrelated(self):
  self.assertFalse(evaluate("宇宙について研究する人がいる","MECHANISM")["answerable"])
 def test_reject_short(self):
  self.assertFalse(evaluate("高感度","MECHANISM")["answerable"])
 def test_unsupported_intent(self):
  self.assertFalse(evaluate("医療現場では脳磁図の測定に利用されている","OTHER")["answerable"])
 def test_expansion_reject_application(self):
  r=expand(WIKI,"何に使われるの？",fetch=api("超伝導量子干渉計は弱い磁場の検出に用いられる非常に高感度な磁気センサの一種である。"))
  self.assertEqual(r["status"],"NO_ANSWERABLE_EVIDENCE")
 def test_expansion_reject_mechanism(self):
  r=expand(WIKI,"なぜ高感度なの？",fetch=api("超伝導量子干渉計とはジョセフソン接合を含む高感度な磁気センサの一種である。"))
  self.assertEqual(r["status"],"NO_ANSWERABLE_EVIDENCE")
 def test_expansion_accept_use(self):
  r=expand(WIKI,"何に使われるの？",fetch=api("超伝導量子干渉計は医療現場で脳磁図の測定に利用される。"))
  self.assertEqual(r["status"],"FOUND")
 def test_expansion_no_train(self):
  r=expand(WIKI,"何に使われるの？",fetch=api("超伝導量子干渉計は医療現場で脳磁図の測定に利用される。"))
  self.assertFalse(r["train_ready"])
if __name__=="__main__":unittest.main()

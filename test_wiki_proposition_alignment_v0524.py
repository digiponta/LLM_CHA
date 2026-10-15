import unittest
from wiki_proposition_alignment_v0524 import proposition,align
from wiki_evidence_expansion_v0521 import expand

WIKI={"status":"FOUND","title":"超伝導量子干渉計","url":"https://ja.wikipedia.org/wiki/超伝導量子干渉計"}
def fetch(extract):
 return lambda _url:{"query":{"pages":[{"title":"超伝導量子干渉計","extract":extract}]}}
class PropositionAlignmentTests(unittest.TestCase):
 def test_variant(self):
  self.assertEqual(proposition("RF SQUIDは感度が低い")["subject"],"RF SQUID")
 def test_high(self):
  self.assertEqual(proposition("SQUIDは高感度")["polarity"],"HIGH")
 def test_low(self):
  self.assertEqual(proposition("SQUIDは感度が低い")["polarity"],"LOW")
 def test_implicit_subject(self):
  r=align("なぜ高感度なの？","超伝導の量子干渉によって微弱な磁場を検出する","MECHANISM",subject="SQUID")
  self.assertTrue(r["aligned"])
 def test_subject_mismatch(self):
  r=align("なぜ高感度なの？","RF SQUIDは超伝導の量子干渉によって微弱な磁場を検出する","MECHANISM",subject="SQUID")
  self.assertEqual(r["reason"],"SUBJECT_MISMATCH")
 def test_polarity_mismatch(self):
  r=align("なぜ高感度なの？","SQUIDは量子干渉により感度が低い","MECHANISM",subject="SQUID")
  self.assertEqual(r["reason"],"POLARITY_MISMATCH")
 def test_cause_missing(self):
  r=align("なぜ高感度なの？","SQUIDは超伝導を用いた高感度センサーである","MECHANISM",subject="SQUID")
  self.assertEqual(r["reason"],"CAUSAL_RELATION_UNSUPPORTED")
 def test_no_context(self):
  r=align("なぜ高感度なの？","量子干渉によって微弱な磁場を検出する","MECHANISM")
  self.assertEqual(r["reason"],"UNKNOWN_SUBJECT")
 def test_positive_expansion(self):
  r=expand(WIKI,"なぜ高感度なの？",fetch=fetch("超伝導の量子干渉によって微弱な磁場を検出する。"))
  self.assertEqual(r["status"],"FOUND")
 def test_negative_expansion(self):
  r=expand(WIKI,"なぜ高感度なの？",fetch=fetch("RF SQUIDは単一のジョセフソン接合により動作するため安価だが感度は低い。"))
  self.assertNotEqual(r["status"],"FOUND")
 def test_no_training(self):
  r=expand(WIKI,"なぜ高感度なの？",fetch=fetch("超伝導の量子干渉によって微弱な磁場を検出する。"))
  self.assertFalse(r["train_ready"])
  self.assertFalse(r["verified"])
if __name__=="__main__":unittest.main()

import unittest
from wiki_polarity_gate_v0523 import check
from wiki_evidence_expansion_v0521 import expand

WIKI={"status":"FOUND","title":"超伝導量子干渉計","url":"https://ja.wikipedia.org/wiki/超伝導量子干渉計"}
def fixture(extract):
 return lambda _:{"query":{"pages":[{"title":"超伝導量子干渉計","extract":extract}]}}
class PolarityGateTests(unittest.TestCase):
 def test_variant_reject(self):
  s="RF SQUIDはジョセフソン接合により動作するため安価だが感度は低い"
  self.assertEqual(check("なぜ高感度なの？",s,"MECHANISM")["reason"],"SUBJECT_VARIANT_MISMATCH")
 def test_variant_touching_japanese(self):
  s="RF SQUIDは単一のジョセフソン接合により動作するため製造が安いが感度は低い"
  self.assertEqual(check("なぜ高感度なの？",s,"MECHANISM")["reason"],"SUBJECT_VARIANT_MISMATCH")
 def test_variant_spaced_japanese(self):
  s="DC SQUID は超伝導回路の量子干渉によって微弱な磁場を検出する"
  self.assertEqual(check("なぜ高感度なの？",s,"MECHANISM")["reason"],"SUBJECT_VARIANT_MISMATCH")
 def test_plain_squid_not_variant(self):
  s="SQUIDは超伝導の量子干渉によって微弱な磁場を検出する"
  self.assertTrue(check("なぜ高感度なの？",s,"MECHANISM")["supported"])
 def test_low_reject(self):
  s="超伝導の量子干渉によって感度は低い状態となる"
  self.assertEqual(check("なぜ高感度なの？",s,"MECHANISM")["reason"],"POLARITY_MISMATCH")
 def test_nocausal_reject(self):
  s="ジョセフソン接合のあるSQUIDは高感度磁気センサーの一種である"
  self.assertFalse(check("なぜ高感度なの？",s,"MECHANISM")["supported"])
 def test_positive_mechanism(self):
  s="超伝導の量子干渉によって微弱な磁場を検出する"
  self.assertTrue(check("なぜ高感度なの？",s,"MECHANISM")["supported"])
 def test_other_intent_unaffected(self):
  self.assertTrue(check("用途は？","医療現場で脳磁図の測定に利用される","APPLICATION")["supported"])
 def test_expand_bad_rf(self):
  s="RF SQUIDは単一のジョセフソン接合により動作できるため製造が安いが感度は低い。"
  self.assertEqual(expand(WIKI,"なぜ高感度なの？",fetch=fixture(s))["status"],"NO_SEMANTICALLY_ALIGNED_EVIDENCE")
 def test_expand_good_later(self):
  s=("RF SQUIDは単一のジョセフソン接合により動作できるため製造が安いが感度は低い。"
     "SQUIDは超伝導の量子干渉によって微弱な磁場を検出する。")
  r=expand(WIKI,"なぜ高感度なの？",fetch=fixture(s))
  self.assertEqual(r["status"],"FOUND")
  self.assertIn("量子干渉",r["sentence"])
 def test_no_auto_training(self):
  r=expand(WIKI,"なぜ高感度なの？",fetch=fixture("SQUIDは超伝導の量子干渉によって微弱な磁場を検出する。"))
  self.assertFalse(r["train_ready"])
  self.assertFalse(r["verified"])
if __name__=="__main__":unittest.main()

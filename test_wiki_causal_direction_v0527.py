import unittest
from wiki_causal_direction_v0527 import check_direction
from wiki_evidence_expansion_v0521 import expand
from wiki_multi_article_discovery_v0526 import discover

WIKI={"status":"FOUND","title":"超伝導量子干渉計","url":"https://ja.wikipedia.org/wiki/超伝導量子干渉計"}
MRI="近年、低磁場中の低周波の周波数帯域で高感度な超伝導量子干渉素子（SQUID）や光ポンピング磁力計が開発され、それらの導入と非調和解析、スパースモデリングをはじめとする圧縮センシングによる超解像技術の医用画像処理への導入により低磁場MRIでも実用的な撮像が可能になりつつある"
GOOD="SQUIDは超伝導の量子干渉によって微弱な磁場を検出する"
def api(sentence,related=False):
 def fetch(url):
  if related and "prop=links" in url:
   return {"query":{"pages":[{"title":"超伝導量子干渉計","links":[{"title":"ジョセフソン効果"}]}]}}
  return {"query":{"pages":[{"title":"ジョセフソン効果" if related else "超伝導量子干渉計","extract":sentence+"。"}]}}
 return fetch
class CausalDirectionTests(unittest.TestCase):
 def test_real_mri_failure_case(self):
  r=check_direction("なぜ高感度なの？",MRI,"MECHANISM")
  self.assertFalse(r["supported"])
  self.assertEqual(r["reason"],"CAUSAL_DIRECTION_MISMATCH")
 def test_primary_rejects_mri(self):
  r=expand(WIKI,"なぜ高感度なの？",fetch=api(MRI))
  self.assertNotEqual(r["status"],"FOUND")
 def test_related_rejects_mri(self):
  r=discover(WIKI,"なぜ高感度なの？",fetch=api(MRI,True))
  self.assertEqual(r["status"],"NO_ANSWERABLE_RELATED_EVIDENCE")
 def test_good_causal_evidence(self):
  self.assertTrue(check_direction("なぜ高感度なの？",GOOD,"MECHANISM")["supported"])
 def test_related_good(self):
  self.assertEqual(discover(WIKI,"なぜ高感度なの？",fetch=api(GOOD,True))["status"],"FOUND")
 def test_no_causal_marker(self):
  self.assertEqual(check_direction("なぜ高感度なの？","SQUIDは高感度なセンサである","MECHANISM")["reason"],"NO_CAUSAL_LINK")
 def test_physics_not_explained(self):
  self.assertEqual(check_direction("なぜ高感度なの？","SQUIDを利用することで微弱な磁場を検出する","MECHANISM")["reason"],"CAUSE_NOT_PHYSICAL_MECHANISM")
 def test_effect_not_sensitivity(self):
  self.assertEqual(check_direction("なぜ高感度なの？","量子干渉によって回路が動く","MECHANISM")["reason"],"SENSITIVITY_NOT_EFFECT")
 def test_application_scope(self):
  self.assertTrue(check_direction("何に使われるの？",MRI,"APPLICATION")["supported"])
 def test_unverified(self):
  r=discover(WIKI,"なぜ高感度なの？",fetch=api(GOOD,True))
  self.assertFalse(r["verified"])
  self.assertFalse(r["train_ready"])
if __name__=="__main__":unittest.main()

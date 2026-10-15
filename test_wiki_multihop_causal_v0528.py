import unittest
from wiki_multihop_causal_v0528 import edge,compose
URL="https://ja.wikipedia.org/wiki/超伝導量子干渉計"
def item(sentence):return {"sentence":sentence,"source":URL}
class MultiHopTests(unittest.TestCase):
 def test_chain(self):
  rows=[item("ジョセフソン接合によって量子干渉が生じる"),item("量子干渉によって微弱な磁場を検出する")]
  result=compose("なぜ高感度なの？",rows)
  self.assertEqual(result["status"],"CHAIN_FOUND")
  self.assertEqual(len(result["hops"]),2)
 def test_no_bridge(self):
  rows=[item("ジョセフソン接合によって量子干渉が生じる"),item("磁束の変化によって微弱な磁場を検出する")]
  self.assertEqual(compose("なぜ高感度なの？",rows)["status"],"NO_SUPPORTED_CHAIN")
 def test_reversed(self):
  rows=[item("微弱な磁場によって量子干渉が生じる"),item("量子干渉によってジョセフソン接合が生じる")]
  self.assertEqual(compose("なぜ高感度なの？",rows)["status"],"NO_SUPPORTED_CHAIN")
 def test_mri_not_target(self):
  rows=[item("ジョセフソン接合によって量子干渉が生じる"),item("量子干渉によってMRI撮像が可能になる")]
  self.assertEqual(compose("なぜ高感度なの？",rows)["status"],"NO_SUPPORTED_CHAIN")
 def test_provenance(self):
  r=compose("なぜ高感度なの？",[item("ジョセフソン接合によって量子干渉が生じる"),item("量子干渉によって微弱な磁場を検出する")])
  self.assertEqual([e["source"] for e in r["hops"]],[URL,URL])
 def test_bad_source(self):
  self.assertIsNone(edge("ジョセフソン接合によって量子干渉が生じる","http://example.com"))
 def test_ambiguous_term(self):
  self.assertIsNone(edge("ジョセフソン接合と量子干渉によって微弱な磁場を検出する",URL))
 def test_unknown_term(self):
  self.assertIsNone(edge("未知の原因によって量子干渉が生じる",URL))
 def test_insufficient_hops(self):
  self.assertEqual(compose("なぜ高感度なの？",[item("ジョセフソン接合によって量子干渉が生じる")])["status"],"NO_SUPPORTED_CHAIN")
 def test_no_training(self):
  r=compose("なぜ高感度なの？",[item("ジョセフソン接合によって量子干渉が生じる"),item("量子干渉によって微弱な磁場を検出する")])
  self.assertFalse(r["verified"]);self.assertFalse(r["train_ready"])
 def test_other_question(self):
  self.assertEqual(compose("用途は何？",[])["status"],"NOT_APPLICABLE")
if __name__=="__main__":unittest.main()

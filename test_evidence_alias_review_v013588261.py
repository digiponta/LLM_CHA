import unittest
from evidence_alias_normalization_v013588261 import canonical_subject,composition_value,diagnose
from evaluate_evidence_alias_review_v013588261 import inspect

class AliasTests(unittest.TestCase):
 def test_sphalerite(self):
  self.assertEqual(canonical_subject("スファレライトの化学組成は"),"閃亜鉛鉱")
 def test_cpu(self):
  self.assertEqual(canonical_subject("中央処理装置とは"),"CPU")
 def test_composition(self):
  self.assertEqual(composition_value("閃亜鉛鉱","成分は硫化亜鉛である。")["canonical_value"],"ZnS")
  self.assertEqual(composition_value("水","化学式 H2O で表される。")["canonical_value"],"H2O")
 def test_no_hallucinated_formula(self):
  self.assertIsNone(composition_value("閃亜鉛鉱","美しい宝石として知られる。"))
 def test_diagnostic_alias_match(self):
  r=diagnose("スファレライトの化学組成は",{"topic":"閃亜鉛鉱","excerpt":"閃亜鉛鉱は硫化鉱物である。成分は硫化亜鉛である。"})
  self.assertTrue(r["subject_match"])
  self.assertEqual(r["composition_candidates"][0]["canonical_value"],"ZnS")
 def test_no_auto_approval(self):
  data={"cases":[]}
  self.assertFalse(inspect(data)["holdout_approved"])
if __name__=="__main__":unittest.main()

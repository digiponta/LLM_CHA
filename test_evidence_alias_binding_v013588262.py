import unittest
from evidence_alias_binding_v013588262 import bind
from evaluate_alias_binding_v013588262 import evaluate_real

def evidence(topic,excerpt):
    return {"status":"EVIDENCE","topic":topic,"excerpt":excerpt,
            "url":"https://example.invalid/wiki","trust":"EXTERNAL_UNVERIFIED"}

class AliasBindingTests(unittest.TestCase):
 def test_sphalerite_alias_and_value(self):
  e=evidence("閃亜鉛鉱","閃亜鉛鉱は亜鉛の硫化鉱物である。性質\n成分は硫化亜鉛であり、純粋なものは白色である。")
  r=bind("スファレライトの化学組成は",e)
  self.assertEqual(r["status"],"BOUND_EXTRACT_ACCEPTED")
  self.assertEqual(r["value"],"ZnS")
  self.assertEqual(r["surface_value"],"硫化亜鉛")
 def test_water_formula(self):
  e=evidence("水","水とは、化学式 H2O で表される、水素と酸素の化合物である。")
  self.assertEqual(bind("水の化学組成は",e)["value"],"H2O")
 def test_cpu_alias(self):
  e=evidence("CPU","CPU（中央処理装置）は、コンピュータにおける中心的な処理装置である。")
  self.assertEqual(bind("中央処理装置とは",e)["status"],"BOUND_EXTRACT_ACCEPTED")
 def test_subject_mismatch(self):
  e=evidence("閃亜鉛鉱","閃亜鉛鉱の成分は硫化亜鉛である。")
  self.assertEqual(bind("銀河の化学組成は",e)["status"],"ABSTAIN_SUBJECT_MISMATCH")
 def test_no_unsupported_synthesis(self):
  e=evidence("閃亜鉛鉱","閃亜鉛鉱は美しい宝石として知られている。")
  self.assertEqual(bind("スファレライトの化学組成は",e)["status"],"ABSTAIN_NO_BOUND_EVIDENCE")
 def test_no_false_holdout_approval(self):
  row={"id":"x","question":"水の化学組成は",
       "evidence":evidence("水","水は化学式 H2O で表される化合物である。"),
       "source":{"title":"水"},"review":{"status":"PENDING_HUMAN_REVIEW"}}
  self.assertFalse(evaluate_real({"cases":[row]})["holdout_approved"])
if __name__=="__main__":unittest.main()

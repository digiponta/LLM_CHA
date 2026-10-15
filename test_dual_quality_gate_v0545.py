import json
import unittest
from pathlib import Path
from dual_quality_gate_v0545 import decide
from evaluate_dual_quality_gate_v0545 import evaluate_cases
ROOT=Path(__file__).parent
CASES=json.loads((ROOT/"data"/"wiki_repair_eval_v0543.json").read_text(encoding="utf-8"))["cases"]
class DualGateTests(unittest.TestCase):
 def test_no_evidence_accept(self):
  r=decide("量子力学について教えて","普通の回答",accepted=True,agreement=.9,topic="量子力学")
  self.assertEqual(r["decision"],"ACCEPT")
  self.assertFalse(r["evidence_checked"])
 def test_unsupported_review(self):
  r=decide("SQUIDを教えて","SQUIDは半導体を含む。",accepted=True,agreement=.9,topic="SQUID",evidence_status="UNSUPPORTED")
  self.assertEqual(r["decision"],"EVIDENCE_NEEDED")
  self.assertTrue(r["suggest_wiki"])
 def test_inconclusive_no_override(self):
  r=decide("量子力学について","回答",accepted=True,agreement=.9,topic="量子力学",evidence_status="INSUFFICIENT")
  self.assertFalse(r["suggest_wiki"])
 def test_generation_review(self):
  r=decide("SQUIDの記事","未学習です",accepted=False,agreement=.2,topic="SQUID")
  self.assertEqual(r["decision"],"REVIEW")
 def test_explicit_conflict(self):
  r=decide("SQUIDの記事","回答",accepted=True,agreement=.9,topic="SQUID",evidence_status="CONTRADICTED")
  self.assertEqual(r["decision"],"REVIEW")
 def test_supported(self):
  r=decide("SQUIDの記事","回答",accepted=True,agreement=.9,topic="SQUID",evidence_status="SUPPORTED")
  self.assertEqual(r["decision"],"ACCEPT")
 def test_no_training(self):
  r=decide("SQUIDの記事","回答",accepted=True,agreement=.9,topic="SQUID",evidence_status="UNSUPPORTED")
  self.assertFalse(r["auto_lookup"]);self.assertFalse(r["auto_promote"]);self.assertFalse(r["train_ready"])
 def test_baseline_matrix(self):
  r=evaluate_cases(CASES)["baseline"]
  self.assertEqual((r["tp"],r["fp"],r["tn"],r["fn"]),(3,0,2,1))
 def test_dual_matrix(self):
  r=evaluate_cases(CASES)["dual_gate"]
  self.assertEqual((r["tp"],r["fp"],r["tn"],r["fn"]),(4,0,2,0))
 def test_fixture_only(self):
  r=evaluate_cases(CASES)
  self.assertEqual(r["evaluation"],"FIXTURE_ONLY")
  self.assertFalse(r["external_verification"])
if __name__=="__main__":unittest.main()

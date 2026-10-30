import unittest
from generation_diagnostics_v013588230 import GenerationDiagnostics
class Tests(unittest.TestCase):
 def test_empty(self):
  self.assertEqual(GenerationDiagnostics().report()["cases"],0)
  self.assertIsNone(GenerationDiagnostics().report()["acceptance_rate"])
 def test_rates(self):
  d=GenerationDiagnostics()
  d.record("ACCEPT_SOURCE_EXTRACT",candidate="引用",final="引用")
  d.record("REJECT_UNKNOWN",candidate="未学習です",final="出典")
  d.record("REJECT_NOT_ENTAILED",candidate="独自主張",final="出典")
  d.record("REJECT_UNGROUNDED",candidate="未検証",final="出典")
  r=d.report()
  self.assertEqual(r["cases"],4)
  self.assertEqual(r["acceptance_rate"],0.25)
  self.assertEqual(r["fallback_rate"],0.75)
  self.assertEqual(r["unknown_rate"],0.25)
  self.assertEqual(r["evidence_rejection_rate"],0.5)
 def test_metadata_not_content(self):
  d=GenerationDiagnostics()
  x=d.record("REJECT_UNKNOWN",topic="宇宙",candidate="private notes",final="fallback")
  self.assertNotIn("private notes",str(x))
  self.assertEqual(x["candidate_chars"],13)
 def test_reset(self):
  d=GenerationDiagnostics();d.record("NO_MODEL")
  d.reset();self.assertEqual(d.report()["cases"],0)
 def test_comparison_not_automated_quality(self):
  d=GenerationDiagnostics()
  self.assertIn("human-rated",d.comparison()["note"])
if __name__=="__main__":unittest.main()

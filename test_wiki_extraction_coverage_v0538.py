import ast
import unittest
from pathlib import Path
from wiki_extraction_coverage_v0538 import diagnose_body,summarize
U="https://ja.wikipedia.org/wiki/SQUID"
class CoverageTests(unittest.TestCase):
 def test_extracted(self):
  r=diagnose_body("SQUIDはジョセフソン接合を含む。",U)
  self.assertEqual(r["counts"]["EXTRACTED"],1)
  self.assertEqual(r["counts"]["propositions"],1)
 def test_unsupported_grammar(self):
  r=diagnose_body("ジョセフソン接合による磁束検出の仕組みを説明する。",U)
  self.assertEqual(r["counts"]["SUBJECT_OR_COPULA_NOT_RECOGNIZED"],1)
 def test_complex_clause(self):
  r=diagnose_body("SQUIDは微弱な磁場を検出し、医療にも利用される。",U)
  self.assertEqual(r["counts"]["COMPLEX_CLAUSE"],1)
 def test_non_supported(self):
  r=diagnose_body("SQUIDは極めて高い感度を持っている。",U)
  self.assertEqual(r["counts"]["UNSUPPORTED_PATTERN"],1)
 def test_provenance(self):
  r=diagnose_body("SQUIDは極めて高い感度を持っている。",U)
  self.assertEqual(r["samples"][0]["source"],U)
 def test_bounded(self):
  r=diagnose_body("SQUIDは高感度な装置である。\nSQUIDは低温で動作する。",U,sample_limit=1)
  self.assertEqual(len(r["samples"]),1)
 def test_no_trust_change(self):
  r=diagnose_body("SQUIDはジョセフソン接合を含む。",U)
  self.assertFalse(r["verified"]);self.assertFalse(r["train_ready"])
 def test_comparison_summary(self):
  r=summarize({"status":"EVIDENCE_COLLECTED","articles":[{}],"propositions":[{}],
    "comparison":[{"status":"MATCH"},{"status":"COMPLEMENT"}]})
  self.assertEqual(r["comparison_counts"]["MATCH"],1)
  self.assertEqual(r["comparison_counts"]["COMPLEMENT"],1)
  self.assertFalse(r["causal_answer_approved"])
 def test_bad_evidence(self):
  self.assertEqual(summarize({})["status"],"NO_EVIDENCE")
 def test_chat_syntax(self):
  s=(Path(__file__).parent/"chat.py").read_text(encoding="utf-8")
  ast.parse(s);self.assertIn("wiki_article_coverage=",s)
if __name__=="__main__":unittest.main()

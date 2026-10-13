"""Regression for v0.4.28.1 diagnostic-only score safety."""
import math
import unittest
from persona_answer_relevance_v0419 import diagnose_relevance
from persona_response_shadow_v0421 import evaluate

class RelevanceHardeningTests(unittest.TestCase):
    def test_negative_cosine_is_valid(self):
        r=diagnose_relevance("読書は好き？","好き。",agreement=0.5,semantic_agreement=-0.4)
        self.assertTrue(r["diagnostic_scores_valid"])
        self.assertEqual(r["semantic_agreement"],-0.4)
    def test_invalid_lexical_fails_diagnostic_only(self):
        for a in (-0.1,1.1,float("nan"),float("inf"),None,"0.3",True):
            with self.subTest(a=a):
                r=diagnose_relevance("読書は好き？","好き。",agreement=a,semantic_agreement=0.8)
                self.assertFalse(r["diagnostic_scores_valid"])
                self.assertTrue(r["relevance_warning"])
                self.assertFalse(r["modifies_truth_gate"])
    def test_invalid_semantic_fails_diagnostic_only(self):
        for s in (-1.1,1.1,float("nan"),float("-inf"),None,False):
            with self.subTest(s=s):
                r=diagnose_relevance("読書は好き？","好き。",agreement=0.5,semantic_agreement=s)
                self.assertFalse(r["diagnostic_scores_valid"])
                self.assertIsNone(r["semantic_agreement"])
    def test_shadow_no_invalid_score_crash(self):
        for score in (None,float("nan"),-2.0):
            with self.subTest(score=score):
                r=evaluate("読書は好き？","好き。",agreement=0.5,semantic_agreement=score,accepted=True)
                self.assertTrue(r["decision_unchanged"])
                self.assertFalse(r["truth_gate_modified"])
    def test_shadow_valid_divergence_unchanged(self):
        r=evaluate("読書は好き？","好き。",agreement=0.1,semantic_agreement=0.9,accepted=True)
        self.assertIn("AGREEMENT_DIVERGENCE",r["flags"])
    def test_boundary_values(self):
        for s in (-1.0,0.0,1.0):
            r=diagnose_relevance("読書は好き？","好き。",agreement=0,semantic_agreement=s)
            self.assertTrue(r["diagnostic_scores_valid"])

if __name__=="__main__":unittest.main()

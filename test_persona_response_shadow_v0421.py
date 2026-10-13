import unittest
from pathlib import Path
from persona_response_shadow_v0421 import evaluate

class ShadowEvaluationTests(unittest.TestCase):
    def test_divergent_but_appropriate(self):
        r=evaluate("今日は何をしていたの","特に変化はない。",
                   agreement=.333,semantic_agreement=.850,accepted=True)
        self.assertIn("AGREEMENT_DIVERGENCE",r["flags"])
        self.assertTrue(r["accepted_by_runtime"])
        self.assertTrue(r["decision_unchanged"])
    def test_irrelevant_fragment(self):
        r=evaluate("貴方は誰","連載後半は対話。 |読切・",
                   agreement=.032,semantic_agreement=.881,accepted=True)
        self.assertIn("OUTPUT_FRAGMENT_MARKERS",r["flags"])
        self.assertIn("IDENTITY_MISMATCH",r["flags"])
    def test_clean(self):
        r=evaluate("こんにちは","こんにちは。",
                   agreement=.9,semantic_agreement=.9,accepted=True)
        self.assertFalse(r["needs_review"])
    def test_not_overridden(self):
        r=evaluate("こんにちは","未学習です",
                   agreement=0,semantic_agreement=0,accepted=False)
        self.assertFalse(r["accepted_by_runtime"])
        self.assertTrue(r["decision_unchanged"])
        self.assertIn("ABSTENTION",r["flags"])
    def test_bad_scores(self):
        with self.assertRaises(ValueError):
            evaluate("q","a",agreement=-1,semantic_agreement=.9,accepted=True)
    def test_bad_accepted(self):
        with self.assertRaises(ValueError):
            evaluate("q","a",agreement=.9,semantic_agreement=.9,accepted=1)
    def test_readonly(self):
        r=evaluate("今日は何をしていたの","特に変化はない。",
                   agreement=.333,semantic_agreement=.85,accepted=True)
        self.assertEqual(r["mode"],"SHADOW_ONLY")
        self.assertFalse(r["truth_gate_modified"])
        self.assertEqual(r["semantic_memory_writes"],0)
        self.assertFalse(r["training_enabled"])
    def test_chat_hook(self):
        s=(Path(__file__).parent/"chat.py").read_text(encoding="utf-8")
        self.assertIn("shadow = evaluate_persona_shadow(",s)
        self.assertIn('if shadow["needs_review"]:',s)
        self.assertLess(s.index("shadow = evaluate_persona_shadow("),
                        s.index('print(f"AI> {reply}")'))
if __name__=="__main__":unittest.main()

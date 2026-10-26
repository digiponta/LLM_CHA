import unittest
from clipboard_composition_evidence_v09756 import CompositionContext
from clipboard_context_v0976 import ClipboardContext

SOURCE="スファレライトは化学組成が硫化亜鉛（ZnS）の鉱物で、閃亜鉛鉱とも呼ばれます。"

class ClipboardChemistryTests(unittest.TestCase):
    def test_explicit_question(self):
        c=CompositionContext()
        self.assertIn("ZnS",c.answer("スファレライトの成分は",SOURCE))
    def test_followup(self):
        c=CompositionContext()
        c.answer("スファレライトの成分は",SOURCE)
        self.assertIn("ZnS",c.answer("化学組成を知りたい",SOURCE))
    def test_after_unrelated_preference(self):
        c=CompositionContext()
        c.answer("スファレライトの成分は",SOURCE)
        self.assertIsNone(c.answer("宝石としてのスファレライトが好きです",SOURCE))
        self.assertIsNone(c.answer("きれいです",SOURCE))
        self.assertIn("ZnS",c.answer("化学組成を知りたい",SOURCE))
    def test_missing_evidence_not_hallucinated(self):
        c=CompositionContext()
        r=c.answer("スファレライトの成分は","スファレライトは美しい鉱物です。")
        self.assertIn("確認できなかった",r)
        self.assertNotIn("ZnS",r)
    def test_other_zns_not_attributed(self):
        c=CompositionContext()
        src="スファレライトは宝石です。" + "A"*400 + "別の試料は硫化亜鉛（ZnS）の鉱物です。"
        r=c.answer("スファレライトの成分は",src)
        self.assertNotIn("ZnS",r)
    def test_no_topic_for_bare_composition(self):
        self.assertIsNone(CompositionContext().answer("化学組成を知りたい",SOURCE))
    def test_clipboard_integration(self):
        c=ClipboardContext()
        c.set(SOURCE)
        self.assertIn("ZnS",c.answer("スファレライトの成分"))
        self.assertIn("ZnS",c.answer("化学組成を知りたい"))
    def test_reset_on_new_clipboard(self):
        c=ClipboardContext()
        c.set(SOURCE)
        c.answer("スファレライトの成分")
        c.set("別のページ")
        self.assertIsNone(c.composition.topic)
    def test_no_trust_promotion(self):
        r=CompositionContext().answer("スファレライトの成分",SOURCE)
        self.assertIn("未検証",r)
if __name__=="__main__":unittest.main()

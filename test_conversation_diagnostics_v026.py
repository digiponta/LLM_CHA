import unittest
from conversation_diagnostics_v026 import classify_quality,prompt_debug

class DiagnosticTests(unittest.TestCase):
    def test_generic_context_rejected_diagnostic(self):
        r=classify_quality("その話、続けて","そうですね。")
        self.assertTrue(r["flag"])
        self.assertTrue(r["context_required"])
    def test_good_non_generic(self):
        self.assertFalse(classify_quality("本は好き？","科学に関する本が好きです。")["flag"])
    def test_prompt_contains_transient_context(self):
        result=prompt_debug("人: SFです。その話、続けて\nAI:",1,True)
        self.assertIn("SFです",result)
        self.assertIn("transient_context=True",result)
    def test_no_accidental_gate_change(self):
        self.assertTrue(classify_quality("その話、続けて","そうですね")["flag"])
if __name__=="__main__":unittest.main()

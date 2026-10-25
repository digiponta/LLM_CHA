import unittest
from clipboard_context_v0976 import ClipboardContext
from clipboard_generic_evidence_v09711 import answer

TEXT=("研究紹介\n"
      "Semantic Operating Systems は意味に基づいてタスクを扱う仕組みを検討する。\n"
      "Quantum Hyper-Aether は仮想マシンとLLMの協調を研究する。\n"
      "研究ノートは仮説を記載しており未検証である。\n")
class GenericClipboardTests(unittest.TestCase):
    def test_quotes_source_text(self):
        r=answer("このページでSemantic Operating Systemsについて記述は？",TEXT)
        self.assertIn("Semantic Operating Systems",r["answer"])
        self.assertFalse(r["train_ready"])
    def test_unrelated_routing_preserved(self):
        self.assertIsNone(answer("こんにちは",TEXT))
    def test_context_integration(self):
        c=ClipboardContext()
        c.set(TEXT)
        self.assertIn("Quantum Hyper-Aether",c.answer("このページでQuantum Hyper-Aetherについて記述は？"))
    def test_empty(self):
        self.assertIsNone(answer("このページで研究について記述は？",""))
if __name__=="__main__":unittest.main()

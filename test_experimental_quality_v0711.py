import ast
import unittest
from pathlib import Path
from experimental_quality_gate_v0711 import quality_gate,fallback_on_structured_unknown

class QualityGateTests(unittest.TestCase):
    def test_prior_nonsense_rejected(self):
        for question,answer in [
          ("トヨタとは","候補の実験回答回収録答回答回答回答回答回お途中核で、回の更新の実験回帰回継続時間"),
          ("猫","ネコ: コェル落。候補。候補に。"),
          ("宇宙","宇宙全体を時間的な量化回の結果。"),
        ]:
            self.assertFalse(quality_gate(question,answer)[0])
    def test_regression_rejection_reasons(self):
        self.assertEqual(quality_gate("宇宙","宇宙全体を時間的な量化回の結果。")[1],"malformed_generation")
        self.assertEqual(quality_gate("猫","ネコ: コェル落。候補。候補に。")[1],"malformed_generation")
    def test_unverified_answer_remains_unverified(self):
        r=fallback_on_structured_unknown("トヨタとは",lambda q:"トヨタは自動車メーカーです。",allow=True)
        self.assertEqual(r["truth_state"],"EXPERIMENTAL_UNVERIFIED")
        self.assertFalse(r["auto_promote"])
    def test_optin_required(self):
        def forbidden(q):raise AssertionError("should never call")
        self.assertIsNone(fallback_on_structured_unknown("猫",forbidden))
    def test_rejected_answer_becomes_unknown(self):
        r=fallback_on_structured_unknown("トヨタとは",lambda q:"回答回答回答回答回答回答",allow=True)
        self.assertEqual(r["truth_state"],"UNKNOWN")
        self.assertIsNone(r["answer"])
    def test_guard_is_executable_code_not_comment(self):
        import ast
        tree=ast.parse(Path(__file__).with_name("experimental_quality_gate_v0711.py").read_text(encoding="utf-8"))
        names=[node.value for node in ast.walk(tree) if isinstance(node,ast.Constant) and isinstance(node.value,str)]
        self.assertIn("malformed_generation",names)
    def test_runtime_wiring_is_parseable(self):
        source=Path(__file__).with_name("chat.py").read_text(encoding="utf-8")
        ast.parse(source)
        self.assertIn('resolution_name == "UNKNOWN_KNOWLEDGE"',source)
        self.assertIn('LLM_CHA_EXPERIMENTAL_FALLBACK',source)
        self.assertIn('fallback_on_structured_unknown(',source)
if __name__=="__main__":unittest.main()

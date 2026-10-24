import ast
import unittest
from pathlib import Path

class EquationIntentTests(unittest.TestCase):
    def test_runtime_wiring(self):
        source=Path(__file__).with_name("chat.py").read_text(encoding="utf-8")
        ast.parse(source)
        self.assertIn('"数式の意味", "数式を説明", "数式について教えて"',source)
        self.assertIn('route = "EQUATION_EVIDENCE_INSUFFICIENT"',source)
        self.assertLess(source.index("EQUATION_EVIDENCE_ON_DEMAND"),source.index("identity_result = identity_context.respond(user_text)"))

if __name__=="__main__":
    unittest.main()

import ast
import unittest
from pathlib import Path

class EquationRuntimeTests(unittest.TestCase):
    def test_runtime_wiring(self):
        text=Path(__file__).with_name("chat.py").read_text(encoding="utf-8")
        ast.parse(text)
        self.assertIn("cha_wiki_equation_cursor = EquationCursor()",text)
        self.assertIn("cha_wiki_equation_cursor.next(cha_wiki_conversation.current)",text)
        self.assertIn("quality_gate=SOURCE_WIKITEXT_MATH_EXACT",text)

if __name__=="__main__":
    unittest.main()

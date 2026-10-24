import ast
import unittest
from pathlib import Path

class PendingEquationFollowupTests(unittest.TestCase):
    def test_runtime_wiring_and_order(self):
        source=Path(__file__).with_name("chat.py").read_text(encoding="utf-8")
        ast.parse(source)
        self.assertIn("pending_equation_explanation = None",source)
        self.assertIn("EQUATION_SEMANTIC_FOLLOWUP",source)
        self.assertIn('route == "EQUATION_EVIDENCE_ON_DEMAND"',source)
        self.assertLess(source.index("EQUATION_SEMANTIC_FOLLOWUP"),source.index("wiki_followup=cha_wiki_conversation.respond"))
    def test_identity_check(self):
        source=Path(__file__).with_name("chat.py").read_text(encoding="utf-8")
        self.assertIn('wiki_now.get("title"), wiki_now.get("url")',source)

if __name__=="__main__":
    unittest.main()

import ast
import unittest
from pathlib import Path

class SynonymRuntimeWiringTests(unittest.TestCase):
    def test_chat_hook_parses_and_uses_recovery(self):
        source=Path(__file__).with_name("chat.py").read_text(encoding="utf-8")
        ast.parse(source)
        self.assertIn("recover_bare_synonym(",source)
        self.assertIn('cha_quality_guard_status == "LOW_SIGNAL_REJECT"',source)
        self.assertIn('cha_quality_guard_status = "SYNONYM_WIKIPEDIA_RECOVERY"',source)
        self.assertIn("accepted = False",source)
        self.assertIn("truth_allows_direct_retrieval(",source)

if __name__=="__main__":
    unittest.main()

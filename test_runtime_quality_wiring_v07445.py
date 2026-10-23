"""Static integration invariants; real GPU acceptance must run separately."""
import ast
import unittest
from pathlib import Path

class RuntimeQualityGateWiringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = Path(__file__).with_name("chat.py").read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.source)

    def test_gate_is_opt_in(self):
        self.assertIn('os.environ.get("LLM_CHA_RESPONSE_GATE", "0") == "1"',self.source)

    def test_gate_occurs_before_display(self):
        hook = self.source.index("# v0.7.44.5 opt-in guard")
        display = self.source.index('print(f"AI> {reply}")',hook)
        self.assertLess(hook,display)

    def test_gate_excludes_candidate_fallback(self):
        hook=self.source.index("# v0.7.44.5 opt-in guard")
        display=self.source.index('print(f"AI> {reply}")',hook)
        self.assertIn("candidate_fallback is None",self.source[hook:display])

    def test_failed_output_not_marked_accepted(self):
        hook=self.source.index("# v0.7.44.5 opt-in guard")
        display=self.source.index('print(f"AI> {reply}")',hook)
        self.assertIn("accepted = False",self.source[hook:display])

if __name__=="__main__":
    unittest.main()

"""v0.7.44.6 regression of the opt-in live audit hook."""
import ast
import unittest
from pathlib import Path

class PersonaSignalWiringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=Path(__file__).with_name("chat.py").read_text(encoding="utf-8")
        ast.parse(cls.source)
        begin=cls.source.index("# v0.7.44.5 opt-in guard")
        end=cls.source.index('print(f"AI> {reply}")',begin)
        cls.hook=cls.source[begin:end]
    def test_live_persona_audit(self):
        self.assertIn('cha_persona_audit(',self.hook)
        self.assertIn('cha_persona_raw_audit.get("persona_gap")',self.hook)
    def test_no_fixed_false_gap(self):
        self.assertNotIn("reply, persona_gap=False",self.hook)
    def test_low_confidence_rejection(self):
        self.assertIn("primary.min_confidence < 0.10",self.hook)
        self.assertIn("agreement < 0.10",self.hook)
        self.assertIn('"LOW_SIGNAL_REJECT"',self.hook)
    def test_no_candidate_fallback_interception(self):
        self.assertIn("candidate_fallback is None",self.hook)
    def test_rejected_not_trained(self):
        self.assertIn("accepted = False",self.hook)

if __name__=="__main__":
    unittest.main()

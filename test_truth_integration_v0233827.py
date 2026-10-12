"""v0.2.33.82.7 source integration regressions."""
import ast
from pathlib import Path
import unittest

class TruthIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = Path(__file__).with_name("chat.py").read_text(encoding="utf-8")
        ast.parse(cls.source)

    def test_opt_in_overlay(self):
        self.assertIn('TruthOverlay(os.environ.get("LLM_CHA_PROPOSITION_TRUTH"))', self.source)

    def test_subject_truth_first(self):
        self.assertIn('truth_allows_direct_retrieval(', self.source)
        self.assertIn('retrieval_truth.state, True', self.source)

    def test_both_paths_check_proposition(self):
        self.assertIn('followup_subject, proposition, followup_hit.provenance', self.source)
        self.assertIn('retrieval_focus, shown, retrieval.provenance', self.source)

    def test_warning_uses_proposition_truth(self):
        self.assertIn('if decision.state == "UNVERIFIED"', self.source)

    def test_blocks_without_generator(self):
        self.assertIn('[grounded-expansion=BLOCKED]', self.source)
        self.assertIn('[proposition truth=BLOCK', self.source)

if __name__=="__main__": unittest.main()

import pathlib
import unittest
ROOT=pathlib.Path(__file__).resolve().parent
SOURCE=(ROOT/"chat.py").read_text(encoding="utf-8")
class RecoveryIntegrationTests(unittest.TestCase):
    def test_disabled_by_default(self):
        self.assertIn('os.environ.get("LLM_CHA_CONTEXT_RECOVERY", "0") == "1"',SOURCE)
    def test_only_when_multitopic(self):
        self.assertIn('if topic_adapter is not None and os.environ.get("LLM_CHA_CONTEXT_RECOVERY"',SOURCE)
    def test_commands_before_legacy_reset(self):
        self.assertLess(SOURCE.index('if command in ("/context-save", "/context-load")'),SOURCE.index('if command == "/reset":'))
    def test_current_truth_reloaded(self):
        self.assertIn('effective_truth_record(truth_store_path, subject)',SOURCE)
        self.assertIn('TruthOverlay(os.environ.get("LLM_CHA_PROPOSITION_TRUTH"))',SOURCE)
    def test_explicit_commands_only(self):
        self.assertIn('if command == "/context-save":',SOURCE)
        self.assertIn('report = context_load(',SOURCE)
    def test_baseline_truth_guard_preserved(self):
        self.assertIn("truth_allows_direct_retrieval(",SOURCE)
        self.assertIn("topic_route = topic_adapter.process_user_turn",SOURCE)
if __name__=="__main__":unittest.main()

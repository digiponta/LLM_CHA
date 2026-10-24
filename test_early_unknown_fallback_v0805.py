import unittest
from pathlib import Path

class EarlyUnknownFallbackTests(unittest.TestCase):
    def test_early_route_before_print(self):
        code=Path(__file__).with_name("chat.py").read_text(encoding="utf-8")
        start=code.index('if resolution_name == "UNKNOWN_KNOWLEDGE" and block_reply == UNKNOWN_REPLY:')
        finish=code.index('print(f"AI> {block_reply}")',start)
        self.assertLess(start,finish)
        self.assertIn("fallback_on_failure(raw_user_text, failed=True)",code[start:finish])
        self.assertIn("UNAPPROVED_SEMANTIC_UNKNOWN_RECOVERY",code[start:finish])
    def test_not_confusing_truth_block(self):
        code=Path(__file__).with_name("chat.py").read_text(encoding="utf-8")
        self.assertIn('resolution_name == "UNKNOWN_KNOWLEDGE" and block_reply == UNKNOWN_REPLY',code)

if __name__=="__main__":
    unittest.main()

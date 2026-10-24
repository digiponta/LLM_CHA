import unittest
from pathlib import Path
class UnknownFallbackRouteTests(unittest.TestCase):
    def test_unknown_reply_connected(self):
        text=Path(__file__).with_name("chat.py").read_text(encoding="utf-8")
        self.assertIn('if reply in (UNKNOWN_REPLY, "回答をうまく生成できませんでした。もう一度質問してください。"):',text)
        self.assertIn('semantic_recovery = fallback_on_failure(raw_user_text, failed=True)',text)
    def test_no_fallback_on_success(self):
        from unapproved_fallback_v0803 import fallback_on_failure
        self.assertEqual(fallback_on_failure("量子ビットとは",False)["status"],"NOT_NEEDED")
if __name__=="__main__":unittest.main()

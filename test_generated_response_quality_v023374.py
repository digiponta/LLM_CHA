import unittest
from generated_response_quality_v023374 import greeting_repair

class QualityTests(unittest.TestCase):
    def test_rejected_greeting(self):
        self.assertEqual(greeting_repair("こんにちは","未学習です",False)[0],"こんにちは。")
    def test_garbled_accepted(self):
        self.assertEqual(greeting_repair("こんにちは","こんにちは。元気障で 強く資源、 の後の前に注釈を呈する。",True)[0],"こんにちは。")
    def test_natural_accepted(self):
        self.assertIsNone(greeting_repair("こんにちは","こんにちは。",True)[0])
    def test_fact_no_override(self):
        self.assertIsNone(greeting_repair("宇宙とは","未学習です",False)[0])
    def test_mixed_request_no_override(self):
        self.assertIsNone(greeting_repair("こんにちは、量子力学を教えて","未学習です",False)[0])
    def test_question_no_override(self):
        self.assertIsNone(greeting_repair("おはよう？今日のニュースは","未学習です",False)[0])
    def test_evening(self):
        self.assertEqual(greeting_repair("こんばんは！","",False)[0],"こんばんは。")
    def test_long_accepted(self):
        self.assertEqual(greeting_repair("やあ","こんにちは。"*20,True)[0],"こんにちは。")
    def test_other_persona_not_changed(self):
        self.assertIsNone(greeting_repair("/character select nagato","未学習です",False)[0])
if __name__=="__main__":unittest.main()

import unittest
from prepare_real_persona_pilot_v013588293 import eligible,norm
class PilotTests(unittest.TestCase):
 def test_exact_holdout(self):self.assertEqual(eligible("今日は何をしてる？","会話中です。",{norm("今日は何をしてる？")}),"EXACT_HOLDOUT")
 def test_email_filtered(self):self.assertEqual(eligible("連絡して","abc@example.comです。",set()),"PII_HEURISTIC")
 def test_non_japanese(self):self.assertEqual(eligible("hello","world",set()),"NON_JAPANESE")
 def test_valid(self):self.assertIsNone(eligible("おはよう","おはようございます",set()))
if __name__=="__main__":unittest.main()

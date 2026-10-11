import unittest
from generated_response_quality_v023374 import greeting_repair

class GreetingHardeningTests(unittest.TestCase):
    def test_logged_accepted_garbage(self):
        raw="こんにちは。元気障で 強く資源、 の後の前に注釈を呈する。"
        self.assertEqual(greeting_repair("こんにちは",raw,True)[0],"こんにちは。")
    def test_short_garbage_even_if_greeting_prefix(self):
        self.assertEqual(greeting_repair("こんにちは","こんにちは。意味不明。",True)[0],"こんにちは。")
    def test_accepted_natural_hello(self):
        self.assertEqual(greeting_repair("こんにちは","こんにちは。",True)[0],None)
    def test_rejected_hello(self):
        self.assertEqual(greeting_repair("こんにちは","未学習です",False)[0],"こんにちは。")
    def test_mixed_stays_untouched(self):
        self.assertEqual(greeting_repair("こんにちは、宇宙について教えて","未学習です",False)[0],None)
    def test_knowledge_stays_untouched(self):
        self.assertEqual(greeting_repair("宇宙とは","未学習です",False)[0],None)
    def test_command_stays_untouched(self):
        self.assertEqual(greeting_repair("/character show","未学習です",False)[0],None)
    def test_evening(self):
        self.assertEqual(greeting_repair("こんばんは","こんばんは。",True)[0],None)
    def test_morning(self):
        self.assertEqual(greeting_repair("おはよう","だめな出力",True)[0],"おはようございます。")
if __name__=="__main__":unittest.main()

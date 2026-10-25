import unittest
from semantic_response_gate_v09744 import assess,fallback

class GateTests(unittest.TestCase):
    def test_positive_reversal(self):
        r=assess("今日は楽しかった","悲しかったんだね。")
        self.assertEqual(r.decision,"FALLBACK")
        self.assertIn("良かった",r.selected_response)
    def test_positive_accept(self):
        r=assess("今日は楽しかった","楽しかったんだね。良かった。")
        self.assertEqual(r.decision,"ACCEPT")
    def test_contrast_missing_secondary(self):
        r=assess("嬉しいけれど悲しい","悲しいんだね。")
        self.assertEqual(r.decision,"FALLBACK")
        self.assertIn("嬉し",r.selected_response)
    def test_contrast_correct(self):
        r=assess("嬉しいけれど悲しい","嬉しさもあるけれど悲しい気持ちなんだね。")
        self.assertEqual(r.decision,"ACCEPT")
    def test_negation_reasserted(self):
        r=assess("悲しくない","悲しいんだね。")
        self.assertEqual(r.decision,"FALLBACK")
        self.assertIn("ではない",r.selected_response)
    def test_multi_negation(self):
        r=assess("悲しくないし、不安ではない","不安な気分なんだね。")
        self.assertEqual(r.decision,"FALLBACK")
        self.assertIn("悲しくも",r.selected_response)
    def test_fatigue_and_joy(self):
        r=assess("楽しかったけど疲れた","疲れたんだね。")
        self.assertEqual(r.decision,"FALLBACK")
        self.assertIn("楽しかった",r.selected_response)
    def test_question_fallback(self):
        r=assess("悲しいけれど、どうすればいい？","気分からない?")
        self.assertEqual(r.decision,"FALLBACK")
        self.assertIn("何があった",r.selected_response)
    def test_unknown_abstains(self):
        r=assess("量子力学について教えて","量子力学の説明です。")
        self.assertEqual(r.decision,"ABSTAIN")
    def test_does_not_promote(self):
        r=assess("今日は楽しかった","悲しいんだね。")
        self.assertFalse(r.train_ready or r.auto_promote or r.persisted)
if __name__=="__main__":unittest.main()

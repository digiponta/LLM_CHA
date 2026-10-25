import unittest
from clipboard_context_v0976 import ClipboardContext
from chat import evaluate_unknown_gate
from unittest.mock import patch
from types import SimpleNamespace

MENU="""メニュー
ビバレッジ
ブラックベリー ヨーグルト フラペチーノ® 黒耳 ver.
ブラックベリー ヨーグルト フラペチーノ® 白耳 ver.
ビバレッジ一覧へ
フード
チーズケーキ
フード一覧へ
"""
class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.ctx=ClipboardContext();self.ctx.set(MENU)
    def start(self):
        self.ctx.answer("ブラックベリー ヨーグルト フラペチーノ® 黒耳 ver.を飲んだことがある")
    def test_expiry_clears_product(self):
        self.start()
        self.ctx.answer("酸味と甘さのバランスが良かった")
        self.ctx.answer("黒耳は、ブラックチョコレートで甘かった")
        self.assertEqual(self.ctx.dialogue.taste_turns,0)
        self.assertIsNone(self.ctx.dialogue.experience_product)
    def test_topic_switch_clears_product(self):
        self.start()
        self.ctx.answer("フラペチーノの種類は")
        self.assertIsNone(self.ctx.dialogue.experience_product)
    def test_new_clipboard_clears(self):
        self.start()
        self.ctx.set(MENU)
        self.assertIsNone(self.ctx.dialogue.experience_product)

class GateRegressionTests(unittest.TestCase):
    def gate(self,lexical,semantic):
        sample=SimpleNamespace(text="通常の日本語の応答です。",mean_confidence=.286,
            min_confidence=.07,mean_top2_margin=.165)
        with patch("chat.mean_pairwise_agreement",return_value=lexical),patch(
            "chat.mean_pairwise_semantic_agreement",return_value=semantic):
            return evaluate_unknown_gate(None,None,[sample,sample],
                min_confidence=.18,min_token_confidence=.02,min_mean_margin=.01,
                min_agreement=.35,min_semantic_agreement=.82,allow_semantic_rescue=True)
    def test_observed_bad_rescue_rejected(self):
        result=self.gate(.017,.854)
        self.assertFalse(result[0])
        self.assertEqual(result[4],"extreme lexical probe disagreement")
    def test_semantic_rescue_above_floor(self):
        self.assertTrue(self.gate(.12,.854)[0])
    def test_normal_lexical_accept(self):
        self.assertTrue(self.gate(.40,.50)[0])

if __name__=="__main__":unittest.main()

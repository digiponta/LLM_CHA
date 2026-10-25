import unittest
from clipboard_context_v0976 import ClipboardContext

MENU="""メニュー
ビバレッジ
ブラックベリー ヨーグルト フラペチーノ® 黒耳 ver.
ブラックベリー ヨーグルト フラペチーノ® 白耳 ver.
ビバレッジ一覧へ
フード
チーズケーキ
フード一覧へ
"""
class SemanticStateTests(unittest.TestCase):
    def setUp(self):
        self.ctx=ClipboardContext()
        self.ctx.set(MENU)
    def test_provenance_and_event(self):
        self.ctx.answer("黒耳を飲んだ")
        s=self.ctx.semantic.snapshot()
        self.assertEqual(s["event"],"consumption")
        self.assertEqual(s["entity_provenance"],"CLIPBOARD_UNVERIFIED")
        self.assertEqual(s["actor"],"user")
        self.assertFalse(s["train_ready"])
        self.assertFalse(s["persisted"])
    def test_taste_and_conclusion(self):
        self.ctx.answer("黒耳を飲んだ")
        self.ctx.answer("酸味と甘さのバランスが良かった")
        self.ctx.answer("黒耳は、ブラックチョコレートで甘かった")
        self.ctx.answer("満足した")
        s=self.ctx.semantic.snapshot()
        self.assertEqual(s["status"],"CLOSED")
        self.assertEqual(set(s["attributes"]),{"acidity","sweetness","chocolate"})
        self.assertEqual(s["evaluation"]["value"],"満足した")
        self.assertEqual(s["evaluation"]["provenance"],"USER_REPORTED")
        self.assertIsNone(self.ctx.dialogue.experience_product)
    def test_reset_on_new_clipboard(self):
        self.ctx.answer("黒耳を飲んだ")
        self.ctx.set(MENU)
        self.assertEqual(self.ctx.semantic.snapshot()["status"],"EMPTY")
    def test_unrelated_topic_clears(self):
        self.ctx.answer("黒耳を飲んだ")
        self.ctx.answer("フードの種類は")
        self.assertEqual(self.ctx.semantic.snapshot()["status"],"EMPTY")
    def test_ambiguous_entity_does_not_record(self):
        self.ctx.answer("黒耳と白耳を飲んだ")
        self.assertIsNone(self.ctx.semantic.snapshot()["entity"])
    def test_read_only_snapshot(self):
        self.ctx.answer("黒耳を飲んだ")
        shot=self.ctx.semantic.snapshot()
        shot["attributes"]["forged"]="x"
        self.assertNotIn("forged",self.ctx.semantic.snapshot()["attributes"])
if __name__=="__main__":unittest.main()

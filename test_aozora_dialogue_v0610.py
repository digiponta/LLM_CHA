import unittest
from aozora_dialogue_v0610 import AozoraDialogue

class AozoraDialogueTests(unittest.TestCase):
    def setUp(self):
        self.dialogue=AozoraDialogue({"789":[{"provenance":{"work_id":"789","title":"吾輩は猫である","author":"夏目漱石","card_url":"https://www.aozora.gr.jp/cards/000148/card789.html"},"natural_language_refs":[{"uri":"nl://sample"}],"text":"吾輩は猫である。名前はまだ無い。"}]})
    def test_context_question(self):
        self.dialogue.respond("吾輩")
        result=self.dialogue.respond("猫の名前は")
        self.assertEqual(result[1]["route"],"AOZORA_CONTEXT_FOLLOWUP")
        self.assertIn("名前がありません",result[0])
    def test_cat_general_resolution(self):
        self.assertEqual(self.dialogue.respond("猫")[1]["route"],"CAT_TOPIC_CLARIFY")
        self.assertEqual(self.dialogue.respond("一般的")[1]["route"],"CAT_GENERAL_CLARIFICATION")
    def test_general_question_phrase(self):
        self.dialogue.respond("ネコ")
        answer, metadata = self.dialogue.respond("一般的な質問")
        self.assertEqual(metadata["route"], "CAT_GENERAL_CLARIFICATION")
        self.assertIn("猫の生態", answer)

    def test_general_question_with_punctuation(self):
        self.dialogue.respond("猫")
        result = self.dialogue.respond("一般的な質問。")
        self.assertEqual(result[1]["route"], "CAT_GENERAL_CLARIFICATION")

    def test_cat_literature_resolution(self):
        self.dialogue.respond("猫")
        self.assertEqual(self.dialogue.respond("作品")[1]["route"],"AOZORA_LITERATURE")
    def test_command_unintercepted(self):
        self.assertIsNone(self.dialogue.respond("/exit"))
    def test_unrelated_preserves_runtime(self):
        self.assertIsNone(self.dialogue.respond("宇宙"))
    def test_topic_cleared(self):
        self.dialogue.respond("吾輩")
        self.dialogue.respond("長門")
        self.assertIsNone(self.dialogue.respond("猫の名前は"))

if __name__=="__main__":unittest.main()

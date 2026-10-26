import unittest
from unittest.mock import Mock
from chat_gui_v0119 import ChatGUI, casual_preference_reply, source_question_answer

SOURCE="スファレライトは劈開が完全で、硬度が低いためカットが難しい。屈折率は2.37から2.42と記載されている。"

class MineralDialogueTests(unittest.TestCase):
    def test_cut_grounded(self):
        a=source_question_answer(SOURCE,"なぜカットが難しい")
        self.assertIn("劈開",a)
        self.assertIn("未検証",a)
    def test_refraction_grounded(self):
        a=source_question_answer(SOURCE,"屈折率は？")
        self.assertIn("2.37",a)
    def test_no_unfounded_refraction(self):
        a=source_question_answer("スファレライトの概要。","屈折率は？")
        self.assertIn("記述を確認できません",a)
    def test_preference(self):
        self.assertIn("スファレライト",casual_preference_reply("私は、スファレライトが好きです。"))
    def test_gui_multiturn(self):
        gui=ChatGUI.__new__(ChatGUI)
        gui.entry=Mock()
        gui._append=Mock()
        gui.submit=Mock()
        gui.clipboard_context=SOURCE
        gui.last_clipboard_source=SOURCE
        gui.active_food_item=""
        for q in ("なぜカットが難しい","屈折率は？","私は、スファレライトが好きです。"):
            gui.entry.get.return_value=q
            gui.send()
        self.assertEqual(gui._append.call_count,3)
        self.assertIn("好きなんですね",gui._append.call_args.args[0])
        gui.submit.assert_not_called()
if __name__=="__main__":unittest.main()

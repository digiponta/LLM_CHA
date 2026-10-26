import unittest
from unittest.mock import Mock
from chat_gui_v0119 import ChatGUI

class CLIOutputForwardingTests(unittest.TestCase):
    def gui(self):
        obj=ChatGUI.__new__(ChatGUI)
        obj.chat_ready=False
        obj.line_buffer=""
        obj._append=Mock()
        return obj

    def test_cli_prompt_and_ai_on_same_line(self):
        gui=self.gui()
        gui._show_filtered("startup help text\nYou> ")
        gui._show_filtered("AI> 【未検証の記録】宇宙は膨張している。\n")
        values="".join(call.args[0] for call in gui._append.call_args_list)
        self.assertIn("AI> 【未検証の記録】",values)
        self.assertNotIn("You> AI>",values)

    def test_prompt_and_reply_in_same_chunk(self):
        gui=self.gui()
        gui._show_filtered("help\nYou> AI> こんにちは。\n[retrieval-first=HIT]\n")
        values="".join(call.args[0] for call in gui._append.call_args_list)
        self.assertIn("AI> こんにちは。",values)

    def test_prompt_and_reply_split_arbitrarily(self):
        gui=self.gui()
        for chunk in ("startup\nYo", "u> A", "I> 宇", "宙とは\n"):
            gui._show_filtered(chunk)
        values="".join(call.args[0] for call in gui._append.call_args_list)
        self.assertIn("AI> 宇宙とは",values)

if __name__=="__main__":unittest.main()

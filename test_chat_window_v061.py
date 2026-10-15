import unittest
from chat_window_v061 import ConversationParser

class ConversationParserTests(unittest.TestCase):
    def test_mixed_runtime_log_only_conversation(self):
        events=[]
        parser=ConversationParser(lambda kind, value: events.append((kind,value)))
        stream=("starting runtime\nYou> AI> Wikipediaでは量子状態を扱う。\n"
                "[route=WIKIPEDIA, verified=False]\nYou> AI> 次の説明。\n"
                "[wiki_evidence_session=FOUND]\nYou> ")
        for char in stream:
            parser.feed(char)
        self.assertEqual(events,[
            ("ai","Wikipediaでは量子状態を扱う。"),
            ("ai","次の説明。")])

    def test_multiline_answer_with_latex(self):
        events=[]
        parser=ConversationParser(lambda kind,value: events.append((kind,value)))
        parser.feed("AI> 状態は\nLATEX( |\\psi \\rangle )\nとして表される。\n[route=FOUND]\n")
        self.assertEqual(events,[("ai","状態は"),
                                 ("ai_continuation",r"LATEX( |\psi \rangle )"),
                                 ("ai_continuation","として表される。")])

    def test_partial_prompt(self):
        events=[]
        parser=ConversationParser(lambda kind,value:events.append((kind,value)))
        parser.feed("Yo")
        parser.feed("u> AI> こんにちは。\n")
        self.assertEqual(events,[("ai","こんにちは。")])

    def test_japanese_unicode_line_round_trip(self):
        import io
        from unittest.mock import patch
        from chat_window_v061 import read_terminal_line
        text = "量子ビットとは？\n"
        with patch("chat_window_v061.os.name", "posix"), \
             patch("chat_window_v061.sys.stdin", io.StringIO(text)):
            value = read_terminal_line()
        self.assertEqual(value, text)
        self.assertEqual(value.encode("utf-8").decode("utf-8"), text)

    def test_duplicate_console_prompts(self):
        from chat_window_v061 import ConsolePromptDeduper
        value = "You> You> 量子ビットとは？\nAI> 回答。\nYou> "
        filter_ = ConsolePromptDeduper()
        rendered = "".join(filter_.feed(ch) for ch in value)
        self.assertEqual(rendered, "You> 量子ビットとは？\nAI> 回答。\nYou> ")

    def test_prompt_not_removed_after_output(self):
        from chat_window_v061 import ConsolePromptDeduper
        value = "You> 量子ビットとは？\n[route=OK]\nYou> "
        filter_ = ConsolePromptDeduper()
        rendered = "".join(filter_.feed(ch) for ch in value)
        self.assertEqual(rendered, value)

if __name__=="__main__":
    unittest.main()

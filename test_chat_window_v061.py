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

if __name__=="__main__":
    unittest.main()

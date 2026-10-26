"""GUI v0.9.7.58 clipboard display and route regression."""
import unittest
from chat_window_v061 import ConversationParser
from gui_clipboard_display_v09710 import ClipboardDisplayFilter
from gui_status_v0732 import StatusParser


class ClipboardGuiTests(unittest.TestCase):
    def test_clipboard_read_and_followup_display(self):
        events = []
        display = ClipboardDisplayFilter(lambda kind, value: events.append((kind, value)))
        parser = ConversationParser(display.feed)
        payload = ('You> AI> クリップボードのテキストを読み取りました。\n'
                   '{\n  "route": "CLIPBOARD_CONTEXT_READ",\n'
                   '  "characters": 3983,\n'
                   '  "text": "スファレライトは化学組成が硫化亜鉛（ZnS）の鉱物。"\n'
                   '}\n'
                   '[route=CLIPBOARD_CONTEXT_READ, train_ready=False]\n'
                   'You> AI> コピーした資料には、スファレライトについて「化学組成が硫化亜鉛（ZnS）の鉱物」と記載されています。（クリップボード由来・未検証）\n'
                   '[route=CLIPBOARD_CONTEXT_ANSWER, truth_state=EXTERNAL_UNVERIFIED, train_ready=False]\n'
                   'You> ')
        for char in payload:
            parser.feed(char)
        self.assertEqual(len(events), 2)
        self.assertIn("3983文字", events[0][1])
        self.assertIn("ZnS", events[1][1])
        self.assertNotIn('"route":', events[0][1])

    def test_unverified_route_status(self):
        statuses = []
        parser = StatusParser(lambda values: statuses.append(values))
        for char in "[route=TOPIC_CLIPBOARD_EVIDENCE, truth_state=EXTERNAL_UNVERIFIED, train_ready=False]\n":
            parser.feed(char)
        self.assertIn("TOPIC_CLIPBOARD_EVIDENCE (unverified)", statuses[-1]["route"])

    def test_chat_command_points_to_chat_py(self):
        from chat_window_v061 import build_chat_command
        cmd, label = build_chat_command([])
        self.assertTrue(any(path.endswith("chat.py") for path in cmd))
        self.assertEqual(label, "chat.py default")


if __name__ == "__main__":
    unittest.main()

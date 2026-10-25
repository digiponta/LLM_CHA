import json
import unittest
from gui_clipboard_display_v09710 import ClipboardDisplayFilter
from chat_window_v061 import ConversationParser

class ClipboardDisplayTests(unittest.TestCase):
    def test_compact_summary_preserves_followup(self):
        events=[]
        display=ClipboardDisplayFilter(lambda kind,value: events.append((kind,value)))
        parser=ConversationParser(display.feed)
        payload={"route":"CLIPBOARD_CONTEXT_READ",
                 "text":"スターバックス\\nメニュー","characters":1488,
                 "truncated":False,"train_ready":False}
        stream=("AI> クリップボードのテキストを読み取りました。\n"+
                json.dumps(payload,ensure_ascii=False,indent=2)+"\n"+
                "[route=CLIPBOARD_CONTEXT_READ, train_ready=False]\n"+
                "You> AI> コピーしたページのメニューには、ラテがあります。\nYou> ")
        parser.feed(stream)
        rendered="\n".join(value for kind,value in events)
        self.assertIn("1,488" if False else "1488文字",rendered)
        self.assertIn("コピーしたページのメニュー",rendered)
        self.assertNotIn("content_sha256",rendered)
        self.assertNotIn('"route":',rendered)
    def test_other_answers_untouched(self):
        events=[]
        display=ClipboardDisplayFilter(lambda kind,value:events.append((kind,value)))
        display.feed("ai","こんにちは。")
        self.assertEqual(events,[("ai","こんにちは。")])
    def test_invalid_json_reaches_view(self):
        events=[]
        display=ClipboardDisplayFilter(lambda kind,value:events.append((kind,value)))
        display.feed("ai","クリップボードのテキストを読み取りました。")
        display.feed("ai_continuation","{invalid")
        display.feed("ai","続き")
        self.assertIn(("ai_continuation","{invalid"),events)
if __name__=="__main__":unittest.main()

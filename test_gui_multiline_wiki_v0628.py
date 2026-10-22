import unittest
from chat_window_v061 import ConversationParser

class MultiLineWikiGuiTests(unittest.TestCase):
    def parse(self, text):
        events=[]
        parser=ConversationParser(lambda kind,value:events.append((kind,value)))
        parser.feed(text)
        return events

    def test_article_paragraphs_and_sources(self):
        data=("AI> 【Wikipedia・車／未検証】車（くるま、シャ）\n"
              "\n"
              "輪の形をしており回転するもの。\n"
              "出典: https://ja.wikipedia.org/wiki/%E8%BB%8A\n"
              "【Wikipedia・自動車／未検証】自動車の定義。\n"
              "出典: https://ja.wikipedia.org/wiki/%E8%87%AA%E5%8B%95%E8%BB%8A\n"
              "[route=WIKIPEDIA_SYNONYM_ARTICLES]\n"
              "\nYou> ")
        got=self.parse(data)
        full="\n".join(v for k,v in got)
        self.assertIn("輪の形",full)
        self.assertIn("自動車の定義",full)
        self.assertIn("出典: https://",full)
        self.assertNotIn("[route=",full)

    def test_diagnostic_is_not_rendered(self):
        got=self.parse("AI> 本文\n\n[gate=KNOWN]\n外部のログ\nYou> ")
        self.assertEqual(got,[("ai","本文"),("ai_continuation","")])

    def test_next_answer_starts_new_message(self):
        got=self.parse("AI> 第一段落\n\n第二段落\n[route=x]\nAI> 次の応答\n")
        self.assertEqual([v for k,v in got if k=="ai"],["第一段落","次の応答"])
        self.assertIn(("ai_continuation","第二段落"),got)

if __name__=="__main__":
    unittest.main()

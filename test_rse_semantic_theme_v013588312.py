import unittest
from rse_semantic_theme_v013588312 import select,semantic_features
class ThemeTests(unittest.TestCase):
 def test_conversation_invite(self):
  x=select("少しお話ししませんか？",[{"question":"少し話しませんか？","answer":"もちろん。何について話しましょう？"}])
  self.assertEqual(x["status"],"ANSWER_SELECTED")
  self.assertEqual(x["theme"],"話題")
 def test_unknown(self):
  x=select("スファレライトの化学組成は？",[])
  self.assertEqual(x["status"],"UNLEARNED")
  self.assertEqual(x["answer"],"未学習です")
 def test_hobby_does_not_answer_now(self):
  x=select("今何してる？",[{"question":"最近何をしてる時が楽しい？","answer":"小説を書いているときです。"}])
  self.assertEqual(x["status"],"UNLEARNED")
 def test_personal_answer_rejected(self):
  x=select("明日何をします？",[{"question":"明日何をします？","answer":"明日は実家に帰ります。"}])
  self.assertEqual(x["status"],"UNLEARNED")
 def test_theme_not_enough(self):
  x=select("少しお話ししませんか？",[{"question":"少しお話ししませんか？","answer":"話題なら何でもあります。"}])
  self.assertEqual(x["status"],"UNLEARNED")
 def test_greeting(self):
  x=select("こんばんは",[{"question":"こんばんはー。","answer":"こんばんは！"}])
  self.assertEqual(x["status"],"ANSWER_SELECTED")
if __name__=="__main__":unittest.main()

import unittest
from rerank_question_intent_v0135864 import intent,valence,rerank
class Tests(unittest.TestCase):
 def test_topic_change(self):
  self.assertEqual(intent("別の話を始めてもいい？"),"CHANGE_TOPIC")
  self.assertEqual(intent("その話の続きが聞きたい"),"CONTINUE_TOPIC")
 def test_valence(self):
  self.assertEqual(valence("電子工作で失敗しちゃった"),"DIFFICULTY")
  self.assertEqual(valence("電子工作が楽しい"),"POSITIVE")
 def test_intent_rerank(self):
  hits=[{"rank":1,"id":"a","question":"その話の続きが聞きたい","score":.9211},
        {"rank":2,"id":"b","question":"少し別のことを話そう","score":.9207}]
  out=rerank("別の話を始めてもいい？",hits)
  self.assertEqual(out[0]["id"],"b")
 def test_valence_rerank(self):
  hits=[{"rank":1,"id":"a","question":"電子工作が楽しい","score":.9048},
        {"rank":2,"id":"b","question":"工作が思い通りに進まない","score":.8955}]
  out=rerank("電子工作で失敗しちゃった",hits)
  self.assertEqual(out[0]["id"],"b")
if __name__=="__main__":unittest.main()

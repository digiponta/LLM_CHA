import unittest
from preference_dialogue_v013588210 import PreferenceContext
class PreferenceTests(unittest.TestCase):
 def setUp(self):
  self.c=PreferenceContext(topic="スファレライト")
 def test_topic(self):
  self.assertIn("どんなところ",self.c.respond("私は、スファレライトが好きです。"))
 def test_sparkle(self):
  self.assertIn("輝き",self.c.respond("きらきらしてるところが心地よい"))
 def test_color(self):
  self.assertIn("黄色のスファレライト",self.c.respond("黄色が好きです"))
 def test_no_topic(self):
  self.assertIsNone(PreferenceContext().respond("黄色が好きです"))
 def test_question_passthrough(self):
  self.assertIsNone(self.c.respond("黄色が好きですか？"))
 def test_session_only(self):
  self.c.respond("黄色が好きです")
  self.assertEqual(len(self.c.preferences),1)
  self.assertEqual(len(PreferenceContext().preferences),0)
if __name__=="__main__":unittest.main()

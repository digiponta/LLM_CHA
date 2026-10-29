import unittest
from general_dialogue_intent_v013588219 import GeneralDialogueIntentContext

class Tests(unittest.TestCase):
 def test_color(self):
  c=GeneralDialogueIntentContext();c.observe("どんな色が好き？","スファレライト","スファレライト")
  self.assertIn("黄色",c.respond("黄色","スファレライト"))
 def test_smell(self):
  c=GeneralDialogueIntentContext();c.observe("どんな香りだった？","コーヒー","スターバックス")
  self.assertIn("香り",c.respond("いい香り","スターバックス"))
 def test_texture(self):
  c=GeneralDialogueIntentContext();c.observe("どんな食感？","ケーキ","スターバックス")
  self.assertIn("柔らかい",c.respond("柔らかい","スターバックス"))
 def test_taste(self):
  c=GeneralDialogueIntentContext();c.observe("どんな味だった？","フラペチーノ","スターバックス")
  self.assertIn("おいしかった",c.respond("美味","スターバックス"))
 def test_satisfaction(self):
  self.assertIn("満足",GeneralDialogueIntentContext().respond("満足"))
 def test_explicit_question_passthrough(self):
  c=GeneralDialogueIntentContext();c.observe("どんな味だった？","ケーキ","スターバックス")
  self.assertIsNone(c.respond("美味とは？","スターバックス"))
 def test_topic_change(self):
  c=GeneralDialogueIntentContext();c.observe("どんな味だった？","ケーキ","スターバックス")
  self.assertIsNone(c.respond("美味","スファレライト"))
 def test_one_shot(self):
  c=GeneralDialogueIntentContext();c.observe("どんな香りだった？","ラテ","スターバックス")
  self.assertIsNotNone(c.respond("いい香り","スターバックス"))
  self.assertIsNone(c.respond("いい香り","スターバックス"))
if __name__=="__main__":unittest.main()

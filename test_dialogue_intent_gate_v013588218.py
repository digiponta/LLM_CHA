import unittest
from dialogue_intent_gate_v013588218 import DialogueIntentGate

class Tests(unittest.TestCase):
 def setUp(self):
  self.g=DialogueIntentGate()
 def test_short_taste(self):
  self.g.observe_assistant("どんな味だった？")
  self.assertIn("おいしかった",self.g.respond("美味"))
 def test_knowledge_question(self):
  self.g.observe_assistant("どんな味だった？")
  self.assertIsNone(self.g.respond("美味とは？"))
 def test_no_prompt(self):
  self.assertIsNone(self.g.respond("美味"))
 def test_other_impression(self):
  self.g.observe_assistant("どんな味だった？")
  self.assertIn("印象",self.g.respond("さっぱり"))
 def test_expiry(self):
  self.g.observe_assistant("どんな味だった？")
  self.assertIsNone(self.g.respond("量子力学とは？"))
  self.assertIsNone(self.g.respond("美味"))
 def test_no_repeat(self):
  self.g.observe_assistant("どんな味だった？")
  self.assertIsNotNone(self.g.respond("美味"))
  self.assertIsNone(self.g.respond("美味"))
if __name__=="__main__": unittest.main()

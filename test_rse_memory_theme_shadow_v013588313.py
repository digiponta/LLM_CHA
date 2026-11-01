import unittest
from rse_memory_theme_shadow_v013588313 import decide
class MemoryThemeTests(unittest.TestCase):
 def test_memory_priority(self):
  x=decide("猫とは？",[{"id":"m","query":"猫とは？","answer":"哺乳類です。","approved":True,"verified":True}],[{"question":"猫とは？","answer":"誤った回答"}])
  self.assertEqual(x["status"],"MEMORY_SELECTED")
  self.assertEqual(x["answer"],"哺乳類です。")
 def test_unverified_not_used(self):
  x=decide("猫とは？",[{"query":"猫とは？","answer":"未検証","approved":True,"verified":False}],[])
  self.assertEqual(x["answer"],"未学習です")
 def test_theme_fallback(self):
  x=decide("少しお話ししませんか？",[],[{"question":"少しお話ししませんか？","answer":"もちろん。何について話しましょう？"}])
  self.assertEqual(x["status"],"ANSWER_SELECTED")
 def test_no_match(self):
  x=decide("今何してる？",[],[])
  self.assertEqual(x["status"],"UNLEARNED")
  self.assertFalse(x["live_integration"])
if __name__=="__main__":unittest.main()

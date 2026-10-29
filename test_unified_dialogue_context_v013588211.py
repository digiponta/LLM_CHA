import unittest
from unified_dialogue_context_v013588211 import UnifiedDialogueContext
class ContextTests(unittest.TestCase):
 def test_revisit_gem(self):
  s=UnifiedDialogueContext()
  s.switch("スファレライト");s.switch("スターバックス")
  self.assertEqual(s.resolve("さっきの宝石の黄色が好き"),"スファレライト")
 def test_no_old_topic(self):
  self.assertIsNone(UnifiedDialogueContext().resolve("さっきの宝石の黄色が好き"))
 def test_previous_topic(self):
  s=UnifiedDialogueContext();s.switch("スファレライト");s.switch("スターバックス")
  self.assertEqual(s.resolve("前の話題に戻って"),"スファレライト")
 def test_no_switch_on_same(self):
  s=UnifiedDialogueContext();s.switch("CPU");s.switch("CPU")
  self.assertEqual(s.previous_topics,[])
 def test_bounded(self):
  s=UnifiedDialogueContext()
  for i in range(20):s.switch(str(i))
  self.assertLessEqual(len(s.previous_topics),8)
if __name__=="__main__":unittest.main()

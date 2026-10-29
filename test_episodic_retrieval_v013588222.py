import unittest
from episodic_context_v013588220 import EpisodeContext
from episodic_retrieval_v013588222 import retrieve_episodes,natural_summary
class Tests(unittest.TestCase):
 def setUp(self):
  self.c=EpisodeContext()
  self.c.start("スターバックス","黒耳フラペチーノ","飲んだ")
  self.c.observe("満足","スターバックス")
  self.c.start("スターバックス","カフェアメリカーノ","好み")
  self.c.observe("カフェアメリカーノも好き","スターバックス")
 def test_drink(self):
  answer=retrieve_episodes(self.c,"今まで何を飲んだ？")
  self.assertIn("黒耳フラペチーノ",answer)
  self.assertNotIn("カフェアメリカーノ",answer)
 def test_liked(self):
  self.assertIn("カフェアメリカーノ",retrieve_episodes(self.c,"好きな商品は？"))
 def test_satisfied(self):
  answer=retrieve_episodes(self.c,"どの商品に満足した？")
  self.assertIn("黒耳フラペチーノ",answer)
  self.assertNotIn("カフェアメリカーノ",answer)
 def test_unknown(self):
  self.assertIsNone(retrieve_episodes(self.c,"量子力学とは？"))
 def test_natural(self):
  c=EpisodeContext();e=c.start("スターバックス","ラテ","飲んだ")
  c.observe("香りは良かったけれど、少し苦かった","スターバックス")
  x=natural_summary(e)
  self.assertIn("香りが良かった",x);self.assertIn("少し苦かった",x)
 def test_no_inferred_drinking(self):
  c=EpisodeContext();c.start("スターバックス","カフェアメリカーノ","好み")
  self.assertIn("記録されていません",retrieve_episodes(c,"何を飲んだ？"))
if __name__=="__main__":unittest.main()

import unittest
from episodic_context_v013588220 import EpisodeContext

class EpisodeTests(unittest.TestCase):
 def test_multiple_senses_same_episode(self):
  c=EpisodeContext()
  c.start("スターバックス","黒耳フラペチーノ","飲んだ")
  a=c.observe("香りは良かったが、少し苦かった","スターバックス")
  self.assertEqual(len(a),2)
  dimensions={d for x in a for d in x["dimensions"]}
  self.assertIn("smell",dimensions)
  self.assertIn("taste",dimensions)
  self.assertEqual(len(c.episodes),1)
 def test_emotion_preference(self):
  c=EpisodeContext()
  c.start("スファレライト","黄色の石","見た")
  c.observe("黄色が好き、きらきらして心地よい","スファレライト")
  dims={d for x in c.active.observations for d in x["dimensions"]}
  self.assertIn("vision",dims)
  self.assertIn("preference",dims)
  self.assertIn("emotion",dims)
 def test_topic_preference(self):
  c=EpisodeContext()
  c.observe("スファレライトが好きです","スファレライト")
  self.assertEqual(c.active.subject,"スファレライト")
  self.assertIn("preference",c.active.observations[0]["dimensions"])
 def test_topic_isolation(self):
  c=EpisodeContext();c.start("コーヒー","ラテ","飲んだ")
  self.assertEqual(c.observe("苦かった","スファレライト"),[])
 def test_questions_not_memorized(self):
  c=EpisodeContext();c.start("コーヒー","ラテ","飲んだ")
  self.assertEqual(c.observe("苦味とは？","コーヒー"),[])
 def test_no_external_claim(self):
  c=EpisodeContext();e=c.start("コーヒー","ラテ","飲んだ")
  self.assertEqual(e.evidence_state,"USER_SELF_REPORTED")
 def test_bounded(self):
  c=EpisodeContext(capacity=2)
  for n in ("A","B","C"):c.start("topic",n,"見た")
  self.assertEqual([e.subject for e in c.episodes],["B","C"])
 def test_clear(self):
  c=EpisodeContext();c.start("topic","item","飲んだ");c.clear()
  self.assertEqual(c.episodes,[])
 def test_summary(self):
  c=EpisodeContext();c.start("スターバックス","ラテ","飲んだ")
  c.observe("いい香り","スターバックス")
  self.assertIn("いい香り",c.summary("スターバックス"))
if __name__=="__main__":unittest.main()

import unittest
from social_dialogue_bridge_v01358828 import social_reply
class SocialTests(unittest.TestCase):
 def test_ear(self):
  answer=social_reply("黒耳を飲んだ","スターバックス",["ブラックベリー ヨーグルト フラペチーノ® 黒耳 ver."])
  self.assertIn("ブラックベリー",answer)
 def test_sandwich(self):
  self.assertIn("おいしかった？",social_reply("ハーブソーセージ バゲットサンドを食べた"))
 def test_satisfaction(self):
  self.assertIn("満足",social_reply("満足した"))
 def test_question_passthrough(self):
  self.assertIsNone(social_reply("メニューは？"))
 def test_unrecognized(self):
  self.assertIsNone(social_reply("宇宙とは"))
if __name__=="__main__":unittest.main()

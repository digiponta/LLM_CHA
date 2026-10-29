import unittest
from natural_tool_router_v01358823 import route
class RouterTests(unittest.TestCase):
 def test_google(self):
  self.assertEqual((route("スターバックスをぐぐって").action,route("スターバックスをぐぐって").query),("GOOGLE","スターバックス"))
 def test_wiki(self):
  self.assertEqual(route("スファレライトをWikiで調べて").action,"WIKI")
 def test_clip(self):
  self.assertEqual(route("クリップボードを読み込んで").action,"CLIPBOARD")
 def test_regular_chat(self):
  self.assertIsNone(route("スターバックスについて教えて"))
 def test_commands_guard(self):
  self.assertIsNone(route("/sleep"))
if __name__=="__main__":unittest.main()

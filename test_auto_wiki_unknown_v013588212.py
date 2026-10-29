import io
import json
import unittest
from auto_wiki_unknown_v013588212 import is_unknown_answer,search_term,search_wikipedia,format_result
class FakeResp(io.BytesIO):
 def __enter__(self):return self
 def __exit__(self,*args):self.close()
def fake(payload):
 return lambda req,timeout:FakeResp(json.dumps(payload,ensure_ascii=False).encode())
class WikiTests(unittest.TestCase):
 def test_unknown(self):
  self.assertTrue(is_unknown_answer("未学習です"))
  self.assertFalse(is_unknown_answer("長門有希。"))
 def test_query(self):
  self.assertEqual(search_term("量子力学とは？"),"量子力学")
 def test_topic(self):
  self.assertEqual(search_term("屈折率は？","スファレライト"),"スファレライト")
 def test_hit(self):
  x=search_wikipedia("スファレライト",fake({"query":{"pages":{"1":{"title":"閃亜鉛鉱","extract":"閃亜鉛鉱はスファレライトと呼ばれる鉱物。"}}}}))
  self.assertEqual(x["status"],"HIT")
  self.assertIn("Wikipedia",format_result(x))
 def test_unrelated_filtered(self):
  x=search_wikipedia("スファレライト",fake({"query":{"pages":{"1":{"title":"無関係","extract":"別の作品。"}}}}))
  self.assertEqual(x["status"],"NO_HIT")
 def test_empty(self):
  self.assertEqual(search_wikipedia("不明語",fake({}))["status"],"NO_HIT")
 def test_network_error(self):
  def bad(req,timeout):raise OSError("offline")
  self.assertEqual(search_wikipedia("宇宙",bad)["status"],"ERROR")
if __name__=="__main__":unittest.main()

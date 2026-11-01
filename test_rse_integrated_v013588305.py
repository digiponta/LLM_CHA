import unittest
from rse_integrated_v013588305 import integrate
class RSEIntegrationTests(unittest.TestCase):
 def setUp(self):
  self.rows=[
   {"user":"元気ですかー？","assistant":"元気ですよー！"},
   {"user":"１００マックス元気やとしたらどれぐらいですか？","assistant":"９０くらいですかねー。夕方やからね。あなたは？"},
   {"user":"最近何をしてる時が楽しいですか？","assistant":"なんだろう。小説書いてるときですかねー？"}
  ]
 def test_status_fallback(self):
  r=integrate("最近どう？",self.rows)
  self.assertEqual(r["status"],"SAFE_FALLBACK_PROPOSED")
  self.assertTrue(r["rejected"]>=1)
  self.assertFalse(r["automatic_source_reply"])
 def test_activity_fallback(self):
  r=integrate("今何してる？",self.rows)
  self.assertEqual(r["status"],"SAFE_FALLBACK_PROPOSED")
  self.assertTrue(r["rejected"]>=1)
 def test_invitation_without_source(self):
  r=integrate("少し話さない？",self.rows)
  self.assertEqual(r["candidate_pool"],0)
  self.assertEqual(r["source"],"ASSISTANT_SAFE_TEMPLATE")
 def test_factual_defer(self):
  r=integrate("スファレライトとは？",self.rows)
  self.assertEqual(r["status"],"DEFER_TO_EXISTING_MEMORY")
  self.assertIsNone(r["proposed_response"])
if __name__=="__main__":unittest.main()

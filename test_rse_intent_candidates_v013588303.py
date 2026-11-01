import unittest
from rse_intent_candidates_v013588303 import create_index,rank
class Tests(unittest.TestCase):
 def test_chat_intent_candidates_are_review_only(self):
  ix=create_index([{"user":"最近どう？","assistant":"元気です。"},{"user":"今日は晴れ","assistant":"いいね"}])
  r=rank(ix,"最近どう？")
  self.assertEqual(r["status"],"REVIEW_CANDIDATES")
  self.assertFalse(r["automatic_reply"])
  self.assertNotIn("answer",r["candidates"][0])
 def test_factual_deferred(self):
  ix=create_index([{"user":"最近どう？","assistant":"元気です。"}])
  self.assertEqual(rank(ix,"スファレライトとは？")["target_route"],"SEMANTIC_MEMORY_FIRST")
 def test_personal_experience_warning(self):
  ix=create_index([{"user":"今何してる？","assistant":"私は昨日旅行に行った"}])
  self.assertTrue(rank(ix,"今何してる？")["candidates"][0]["personal_claim_warning"])
 def test_no_match_safe_fallback(self):
  self.assertEqual(rank([],"少し話さない？")["status"],"NO_MATCH")
if __name__=="__main__":unittest.main()

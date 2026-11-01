import unittest
from rse_intent_router_v013588302 import route,evaluate
class IntentTests(unittest.TestCase):
 def test_status(self):
  self.assertEqual(route("最近どう？")["intent"],"STATUS_QUERY")
 def test_invitation(self):
  self.assertEqual(route("少し話さない？")["intent"],"CHAT_INVITATION")
 def test_activity(self):
  self.assertEqual(route("今何してる？")["intent"],"ACTIVITY_QUERY")
 def test_memory_precedence(self):
  self.assertEqual(evaluate("スファレライトとは？")["status"],"DEFER_TO_EXISTING_MEMORY")
 def test_unknown_deferred(self):
  self.assertEqual(evaluate("鉱物の特性を比較")["status"],"DEFER_TO_CONTENT_RSE")
 def test_no_cp_personal_claim(self):
  x=evaluate("今何してる？")
  self.assertFalse(x["persona_claims_from_real_persona_chat"])
  self.assertIn("メッセージ",x["response"])
if __name__=="__main__":unittest.main()

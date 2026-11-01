import unittest
from rse_accept_candidate_v013588307 import assess,benchmark
class AcceptanceTests(unittest.TestCase):
 def test_invitation_candidate_not_auto(self):
  x=assess("少し話さない？","少し話さない？","もちろん、何の話をしましょう？")
  self.assertEqual(x["status"],"ACCEPT_CANDIDATE")
  self.assertFalse(x["auto_reply"])
 def test_persona_transfer_reject(self):
  x=assess("こんにちは","こんにちは","昨日は家族と旅行に行きました")
  self.assertEqual(x["status"],"REJECT")
 def test_activity_remains_manual_or_reject(self):
  x=assess("今何してる？","今何してる？","今は返信中です。")
  self.assertEqual(x["status"],"MANUAL_REVIEW_REQUIRED")
 def test_metrics_and_no_live(self):
  cases=[{"id":"one","query":"こんにちは","source_question":"こんにちは","source_answer":"こんにちは","suitable":True}]
  x=benchmark(cases)
  self.assertEqual(x["accept_candidate_count"],1)
  self.assertFalse(x["live_auto_accept_enabled"])
if __name__=="__main__":unittest.main()

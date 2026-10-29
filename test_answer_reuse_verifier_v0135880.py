import unittest
from answer_reuse_verifier_v0135880 import verify,evaluate
class VerifierTests(unittest.TestCase):
 def test_risky_query_is_reviewed(self):
  self.assertEqual(verify("今日のドル円相場","為替","150円",1)[1],"CURRENT_INFO")
 def test_matching_text_is_not_automatically_accepted(self):
  self.assertEqual(verify("こんにちは","こんにちは","こんにちは",1)[0],"REVIEW")
 def test_followup_requires_context(self):
  self.assertEqual(verify("続きを教えて","説明","続きです",0.8)[1],"CONTEXT_REQUIRED")
 def test_empty_rejected(self):
  self.assertEqual(verify("問い","問い","",0.9)[0],"REJECT")
 def test_bad_score_rejected(self):
  with self.assertRaises(ValueError):verify("問い","問い","回答",1.2)
 def test_evaluation_no_auto_accept(self):
  row={"query_id":"q","candidate_id":"c","query":"こんにちは","candidate_question":"こんにちは","candidate_answer":"はい","score":"1","answer_reusable":"false"}
  self.assertEqual(evaluate([row])["decisions"].get("accepted_incorrect",0),0)
if __name__=="__main__":unittest.main()

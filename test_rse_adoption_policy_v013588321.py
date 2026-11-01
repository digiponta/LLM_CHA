import unittest
from rse_adoption_policy_v013588321 import decide,evaluate_transcript_comparison
class PolicyTests(unittest.TestCase):
 def test_protect_known_atomic(self):
  x=decide(observed_answer="閃亜鉛鉱は、亜鉛の硫化鉱物である。",observed_route="MEMORY_ATOMIC_EXACT",rse_status="MEMORY_PRESENT_UNVERIFIED",rse_answer=None)
  self.assertEqual(x.action,"PRESERVE_EXISTING")
 def test_unapproved_theme_requires_review(self):
  x=decide(observed_answer="無用。お疲れさまでした。",observed_route="normal response",rse_status="ANSWER_SELECTED",rse_answer="もちろん。何について話しましょう？")
  self.assertEqual(x.action,"REVIEW_REQUIRED")
 def test_approved_theme(self):
  x=decide(observed_answer="無用。お疲れさまでした。",observed_route="normal response",rse_status="ANSWER_SELECTED",rse_answer="もちろん。何について話しましょう？",rse_approved=True)
  self.assertEqual(x.action,"SELECT_RSE")
 def test_unknown_abstains(self):
  x=decide(observed_answer="少しだけはとりやすい。",observed_route="normal response",rse_status="UNLEARNED",rse_answer="未学習です")
  self.assertEqual((x.action,x.answer),("ABSTAIN","未学習です"))
 def test_do_not_trust_model_known(self):
  x=decide(observed_answer="無用。お疲れさまでした。",observed_route="KNOWN",rse_status="ANSWER_SELECTED",rse_answer="もちろん。")
  self.assertEqual(x.action,"REVIEW_REQUIRED")
 def test_explicit_truth_restriction(self):
  x=decide(observed_answer=None,observed_route="",rse_status="MEMORY_TRUTH_RESTRICTED",rse_answer=None)
  self.assertEqual(x.action,"REVIEW_REQUIRED")
 def test_report(self):
  report={"cases":[
   {"query":"閃亜鉛鉱とは","observed_chat_answer":"正しい回答","observed_route_lines":["[route=MEMORY_ATOMIC_EXACT]"],"rse_state":"MEMORY_PRESENT_UNVERIFIED"},
   {"query":"少しお話ししませんか？","observed_chat_answer":"無用。","observed_route_lines":[],"rse_state":"ANSWER_SELECTED","rse_answer":"もちろん。"},
   {"query":"今何してる？","observed_chat_answer":"意味不明","observed_route_lines":[],"rse_state":"UNLEARNED"}]}
  x=evaluate_transcript_comparison(report)
  self.assertEqual([t["action"] for t in x["cases"]],["PRESERVE_EXISTING","REVIEW_REQUIRED","ABSTAIN"])
if __name__=="__main__":unittest.main()

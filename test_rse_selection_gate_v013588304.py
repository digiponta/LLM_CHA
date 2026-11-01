import unittest
from rse_selection_gate_v013588304 import gate
class TestRSESelection(unittest.TestCase):
 def test_quantified_answer_rejected(self):
  r=gate("最近どう？","１００マックス元気やとしたらどれぐらいですか？","９０くらいですかねー。夕方やからね。あなたは？")
  self.assertEqual(r["status"],"REJECT")
  self.assertIn("SLOT_MISMATCH_QUANTIFIED_STATE",r["reasons"])
 def test_subjective_human_state_rejected(self):
  r=gate("最近どう？","元気ですかー？","元気ですよー！")
  self.assertIn("POTENTIAL_PERSONA_TRANSFER",r["reasons"])
 def test_enjoyment_current_activity_mismatch(self):
  r=gate("今何してる？","最近何をしてる時が楽しいですか？","なんだろう。小説書いてるときですかねー？")
  self.assertEqual(r["status"],"REJECT")
  self.assertIn("SLOT_MISMATCH_ENJOYMENT",r["reasons"])
 def test_even_clean_candidate_requires_review(self):
  r=gate("少し話さない？","少し話さない？","もちろん。何について話しましょう？")
  self.assertEqual(r["status"],"MANUAL_REVIEW_REQUIRED")
  self.assertFalse(r["response_automatically_approved"])
if __name__=="__main__":unittest.main()

import unittest
from evidence_conditioned_generation_v013588228 import conditioned_prompt, final_answer

class SingleTurnTests(unittest.TestCase):
 def test_one_line(self):
  evidence={"topic":"宇宙","excerpt":"宇宙は膨張している。\n銀河間の距離が伸びる。","status":"EVIDENCE","url":"https://example.org"}
  prompt=conditioned_prompt(evidence)
  self.assertNotIn("\n",prompt)
  self.assertNotIn("\r",prompt)
  self.assertIn("宇宙",prompt)
  self.assertIn("銀河間",prompt)
 def test_strips_topic_newlines(self):
  evidence={"topic":"宇宙\n回答：","excerpt":"説明\r\n続き"}
  self.assertEqual(len(conditioned_prompt(evidence).splitlines()),1)
 def test_input_length_bounded(self):
  evidence={"topic":"量子力学","excerpt":"量子"+"力学"*1000}
  self.assertLess(len(conditioned_prompt(evidence)),320)
 def test_gate_unknown_fallback(self):
  evidence={"status":"EVIDENCE","topic":"宇宙","excerpt":"宇宙は膨張している。","url":"https://example.org"}
  response=final_answer("未学習です",evidence)
  self.assertEqual(response["gate"],"REJECT_UNKNOWN")
  self.assertIn("出典:",response["answer"])
if __name__=="__main__":unittest.main()

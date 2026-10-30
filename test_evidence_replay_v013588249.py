import unittest
from unittest.mock import patch
from compare_evidence_replay_v013588249 import compare
from evidence_aware_route_v013588236 import generation_prompt
class EvidenceReplayTests(unittest.TestCase):
 def test_prompt_matches_cli_route(self):
  self.assertEqual(generation_prompt("宇宙","観測文"),"人: 宇宙を説明してください。参考文: 観測文\nAI:")
 def test_gate_and_same_prompt(self):
  evidence={"status":"EVIDENCE","topic":"宇宙","excerpt":"宇宙は全体として膨張している。","url":"https://example.test/wiki","title":"宇宙"}
  class Result:
   def __init__(self, text):self.text=text;self.token_count=5
  with patch("compare_evidence_replay_v013588249.generate_reply",side_effect=[Result("宇宙は全体として膨張している。"),Result("1967年 APB。")]) as generate,patch("compare_evidence_replay_v013588249.next_token_diagnostic",return_value={}),patch("compare_evidence_replay_v013588249.conditional_nll",return_value=1.0):
   class FakeModel:
   def eval(self):return self
  report=compare(FakeModel(),FakeModel(),object(),evidence,[])
  self.assertEqual(report["base"]["gate"],"ACCEPT_SOURCE_EXTRACT")
  self.assertTrue(report["candidate"]["gate"].startswith("REJECT_"))
  self.assertEqual(generate.call_args_list[0].args[2],generate.call_args_list[1].args[2])
  self.assertEqual(generate.call_args_list[0].kwargs["seed"],0)
if __name__=="__main__":unittest.main()

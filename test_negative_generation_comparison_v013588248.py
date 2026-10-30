import unittest
from pathlib import Path
from unittest.mock import patch
from compare_negative_generation_v013588248 import evaluate_case
class ComparisonTests(unittest.TestCase):
 def test_generation_uses_fixed_seed_greedy(self):
  class Result:
   text="テスト";token_count=2;mean_confidence=0.5
  with patch("compare_negative_generation_v013588248.generate_reply",return_value=Result()) as gen:
   result=evaluate_case(object(),object(),"人: CPUとは\nAI: ",42,96,0.0)
  self.assertEqual(result["text"],"テスト")
  self.assertEqual(gen.call_args.kwargs["seed"],42)
  self.assertEqual(gen.call_args.args[4],0.0)
if __name__=="__main__":unittest.main()

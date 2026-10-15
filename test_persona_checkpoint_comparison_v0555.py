import unittest
from compare_persona_checkpoints_v0555 import prompts,generate_mode,compare
T=[{"user":"今日は散歩した","reference_answer":"どこへ行った？"},{"user":"公園に行った","reference_answer":"何を見た？"}]
class ComparisonTests(unittest.TestCase):
 def test_single(self):
  p=prompts(T,"single");self.assertNotIn("どこへ行った",p[1])
 def test_gold(self):self.assertIn("どこへ行った",prompts(T,"gold")[1])
 def test_self(self):self.assertIn("生成文",prompts(T,"self",["生成文","次"])[1])
 def test_self_needs_outputs(self):
  with self.assertRaises(ValueError):prompts(T,"self")
 def test_deterministic_callback(self):
  r=generate_mode(T,"single",lambda x:"固定応答");self.assertEqual(len(r),2)
 def test_self_history_is_raw(self):
  inputs=[]
  generate_mode(T,"self",lambda x:(inputs.append(x) or "モデル応答"))
  self.assertIn("モデル応答",inputs[1])
 def test_gold_does_not_depend_on_generation(self):
  inputs=[]
  generate_mode(T,"gold",lambda x:(inputs.append(x) or "別回答"))
  self.assertIn("どこへ行った？",inputs[1]);self.assertNotIn("別回答",inputs[1])
 def test_compare(self):
  r=compare({"models":[{"name":"a","path":"x"}],"scenarios":[{"id":"d","turns":T}]},lambda path:(lambda prompt:"モデル応答",{"mock":True}))
  self.assertEqual(len(r["results"][0]["cases"]),3)
 def test_no_forgetting_claim(self):
  r=compare({"models":[],"scenarios":[]},lambda x:None);self.assertFalse(r["claim_of_forgetting"])
 def test_invalid_mode(self):
  with self.assertRaises(ValueError):prompts(T,"invalid")
if __name__=="__main__":unittest.main()

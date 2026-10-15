import ast
import json
import unittest
from pathlib import Path
from evaluate_wiki_repair_v0543 import evaluate_cases
ROOT=Path(__file__).parent
class RepairEvaluationTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.cases=json.loads((ROOT/"data/wiki_repair_eval_v0543.json").read_text(encoding="utf-8"))["cases"]
 def test_six_cases(self):self.assertEqual(len(self.cases),6)
 def test_full_evaluation(self):
  r=evaluate_cases(self.cases)
  self.assertEqual(r["evaluation"],"FIXTURE_ONLY")
  self.assertEqual(r["counts"]["total"],6)
 def test_grounded(self):
  r=evaluate_cases(self.cases)
  self.assertEqual(r["counts"]["grounded"],r["counts"]["eligible"])
 def test_unknown(self):
  r=evaluate_cases(self.cases)
  self.assertEqual(r["counts"]["unknown_total"],2)
  self.assertEqual(r["counts"]["unknown_recovered"],1)
 def test_no_external_claim(self):
  r=evaluate_cases(self.cases)
  self.assertFalse(r["external_verification"])
  self.assertFalse(r["train_ready"])
 def test_no_topic(self):
  r=evaluate_cases(self.cases)
  self.assertFalse(next(x for x in r["details"] if x["id"]=="nonwiki")["suggested"])
 def test_no_wiki_fetch(self):
  text=(ROOT/"evaluate_wiki_repair_v0543.py").read_text(encoding="utf-8")
  self.assertNotIn("from wikipedia_acquisition",text)
 def test_python_syntax(self):
  ast.parse((ROOT/"evaluate_wiki_repair_v0543.py").read_text(encoding="utf-8"))
if __name__=="__main__":unittest.main()

import unittest
from train_offline_replay_ablation_v0135811 import make_plan,WEIGHTS

class OfflineReplayAblationTests(unittest.TestCase):
 def setUp(self):
  self.data={"literature":[f"文{i}" for i in range(300)],
             "conversation":[f"対話{i}" for i in range(60)],
             "knowledge":[f"知識{i}" for i in range(7)],
             "persona":[f"人格{i}" for i in range(23)]}
 def test_all_arms_equal_slots(self):
  plans=make_plan(["A","B","C"],self.data)
  self.assertEqual([len(plans[k][0]) for k in "ABC"],[120]*3)
 def test_B_has_no_persona(self):
  plan=make_plan(["B"],self.data)["B"][1]
  self.assertEqual(plan["line_counts"],{"literature":60,"conversation":48,"knowledge":12})
 def test_C_has_persona(self):
  plan=make_plan(["C"],self.data)["C"][1]
  self.assertEqual(plan["line_counts"]["persona"],12)
 def test_repeatability(self):
  a=make_plan(["A","B","C"],self.data)
  b=make_plan(["A","B","C"],self.data)
  self.assertEqual(a,b)
 def test_reject_missing_rows(self):
  with self.assertRaises(ValueError):
   make_plan(["C"],{**self.data,"persona":[]})
 def test_reject_unknown_arm(self):
  with self.assertRaises(ValueError):make_plan(["D"],self.data)
if __name__=="__main__":unittest.main()

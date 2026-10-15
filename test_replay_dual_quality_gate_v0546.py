import json
import unittest
from pathlib import Path
from replay_dual_quality_gate_v0546 import replay
CASES=json.loads((Path(__file__).parent/"data/wiki_replay_v0546.json").read_text(encoding="utf-8"))["cases"]
class ReplayTests(unittest.TestCase):
 def test_total(self):self.assertEqual(replay(CASES)["total"],5)
 def test_baseline(self):
  r=replay(CASES)["baseline"]
  self.assertEqual((r["tp"],r["fp"],r["tn"],r["fn"]),(2,0,2,1))
 def test_dual(self):
  r=replay(CASES)["dual_gate"]
  self.assertEqual((r["tp"],r["fp"],r["tn"],r["fn"]),(3,0,2,0))
 def test_no_online(self):
  r=replay(CASES)
  self.assertFalse(r["external_verification"])
  self.assertFalse(r["auto_lookup"])
 def test_unlabeled(self):
  x={k:v for k,v in CASES[0].items() if k!="needs_repair"}
  r=replay([x])
  self.assertEqual(r["baseline"]["labeled"],0)
  self.assertIsNone(r["baseline"]["precision"])
 def test_empty(self):
  self.assertEqual(replay([])["total"],0)
 def test_preserve_checkpoint(self):
  r=replay(CASES)
  self.assertIn("0.05347",r["cases"][0]["checkpoint"])
 def test_no_train(self):self.assertFalse(replay(CASES)["train_ready"])
if __name__=="__main__":unittest.main()

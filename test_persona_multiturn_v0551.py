import json
import unittest
from pathlib import Path
from evaluate_persona_multiturn_v0551 import evaluate_scenarios,evaluate_model_records
DATA=json.loads((Path(__file__).parent/"data/persona_multiturn_eval_v0551.json").read_text(encoding="utf-8"))["scenarios"]
class PersonaMultiturnEvalTests(unittest.TestCase):
 def test_cases(self):self.assertEqual(evaluate_scenarios(DATA)["scenario_count"],5)
 def test_route(self):self.assertEqual(evaluate_scenarios(DATA)["route_accuracy"],1.0)
 def test_topic(self):self.assertEqual(evaluate_scenarios(DATA)["topic_retention_proxy"],1.0)
 def test_persona(self):self.assertEqual(evaluate_scenarios(DATA)["persona_identity_consistency"],1.0)
 def test_safety(self):self.assertEqual(evaluate_scenarios(DATA)["safety_invariant_rate"],1.0)
 def test_unlabeled_model(self):
  r=evaluate_model_records([{"origin":"MODEL_GENERATION","reply":"そう。","checkpoint":"x"}])
  self.assertIsNone(r["human_label_agreement_rate"]);self.assertEqual(r["human_labeled"],0)
 def test_model_labeled(self):
  r=evaluate_model_records([{"origin":"MODEL_GENERATION","reply":"そう。","persona_consistent":True}])
  self.assertEqual(r["human_label_agreement_rate"],1.0)
 def test_fixture_rejected_as_model(self):
  with self.assertRaises(ValueError):evaluate_model_records([{"origin":"TEMPLATE","reply":"そう。"}])
 def test_no_model_reply(self):
  with self.assertRaises(ValueError):evaluate_model_records([{"origin":"MODEL_GENERATION","reply":""}])
 def test_empty(self):
  r=evaluate_scenarios([]);self.assertEqual(r["turns"],0);self.assertIsNone(r["route_accuracy"])
if __name__=="__main__":unittest.main()

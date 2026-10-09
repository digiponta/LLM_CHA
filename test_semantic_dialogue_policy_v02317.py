import unittest
from structured_semantic_purpose_v02315 import extract
from semantic_dialogue_policy_v02317 import decide,compare
from evaluate_semantic_dialogue_policy_v02317 import FRESH,evaluate

class DialoguePolicyTests(unittest.TestCase):
    def test_multi_sequential_plan(self):
        self.assertEqual(decide(extract("LLMを勉強してから開発したい")).action,"PLAN")
    def test_multi_unordered_plan(self):
        self.assertEqual(decide(extract("LLMを勉強して開発もしたい")).action,"PLAN")
    def test_casual_respond(self):
        self.assertEqual(decide(extract("Pythonについて雑談したい")).action,"RESPOND")
    def test_ambiguous_confirm(self):
        self.assertEqual(decide(extract("Pythonに興味がある")).action,"ASK_CONFIRMATION")
    def test_unknown_clarify(self):
        self.assertEqual(decide(extract("12345678")).action,"ASK_CLARIFICATION")
    def test_explicit_handoff(self):
        self.assertEqual(decide(extract("LLMを勉強したい")).action,"HANDOFF")
    def test_policy_comparison_shape(self):
        r=compare("Pythonについて雑談したい")
        self.assertIn("old_action",r)
        self.assertIn("new_action",r)
    def test_fixture_and_evaluation(self):
        rows=[{"id":i,"text":t,"expected":a} for i,t,a in FRESH]
        self.assertEqual(len(rows),12)
        self.assertEqual(len(evaluate(rows)),12)
if __name__=="__main__":unittest.main()

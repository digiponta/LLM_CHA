import unittest
from unittest.mock import Mock
from evidence_dialogue_state_v02319 import DialogueState
from contextual_purpose_composition_v02321 import generation_context,step
from dialogue_guided_generation_v02322 import evaluate_turn,prompt_raw,prompt_guided

class DialogueGuidedTests(unittest.TestCase):
    def test_raw_prompt(self):
        self.assertEqual(prompt_raw("Pythonとは"),"人: Pythonとは\nAI: ")
    def test_guided_prompt_has_semantics(self):
        d,a,_=step(DialogueState(),"LLMを勉強してから開発したい")
        c=generation_context(d,a,"LLMを勉強してから開発したい")
        prompt=prompt_guided(c)
        self.assertIn("LLM",prompt)
        self.assertIn("学習 → 開発",prompt)
        self.assertIn("SEQUENTIAL",prompt)
    def test_asks_do_not_generate(self):
        fake=Mock()
        d,row=evaluate_turn(DialogueState(),"Pythonに興味がある",fake)
        self.assertEqual(row["action"],"ASK_CONFIRMATION")
        fake.generate.assert_not_called()
    def test_generation_called_twice(self):
        fake=Mock()
        fake.generate.return_value={"text":"検査用生成","generated_tokens":4,"elapsed_seconds":0.1}
        d,row=evaluate_turn(DialogueState(),"LLMを勉強したい",fake)
        self.assertEqual(fake.generate.call_count,2)
        self.assertEqual(row["variants"]["guided"]["source"],"checkpoint")
        self.assertEqual(row["variants"]["template"]["source"],"deterministic_controller")
        self.assertEqual(row["variants"]["guided"]["text"],"検査用生成")
    def test_no_generator_honest(self):
        _,row=evaluate_turn(DialogueState(),"LLMを勉強したい")
        self.assertIsNone(row["variants"]["guided"]["text"])
        self.assertEqual(row["variants"]["guided"]["source"],"checkpoint_not_loaded")
    def test_multiturn_plan_context(self):
        d=DialogueState()
        d,_=evaluate_turn(d,"LLMを勉強したい")
        d,row=evaluate_turn(d,"それから開発もしたい")
        self.assertEqual(row["action"],"PLAN")
        self.assertEqual(row["dss_purposes"],["learning","development"])
if __name__=="__main__":unittest.main()

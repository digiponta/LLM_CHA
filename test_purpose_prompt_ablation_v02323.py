import unittest
from unittest.mock import Mock
from purpose_prompt_ablation_v02323 import execute,prompt_short,prompt_variants,SCENARIOS
from evidence_dialogue_state_v02319 import DialogueState
from contextual_purpose_composition_v02321 import step,generation_context

class PurposePromptAblationTests(unittest.TestCase):
    def test_three_prompts(self):
        d,a,_=step(DialogueState(),"LLMを勉強したい")
        ctx=generation_context(d,a,"LLMを勉強したい")
        forms=prompt_variants(ctx)
        self.assertEqual(set(forms),{"raw","short","full"})
        self.assertIn("目的: 学習",forms["short"])
        self.assertNotIn("回答方針",forms["short"])
        self.assertIn("回答方針",forms["full"])
    def test_greedy_three_calls(self):
        model=Mock()
        model.generate.return_value={"text":"モデル出力","generated_tokens":3,"elapsed_seconds":0.1}
        result=execute(cases=[("simple",["LLMを勉強したい"])],generator=model)
        self.assertEqual(model.generate.call_count,3)
        self.assertEqual(set(result[0]["variants"]),{"raw","short","full"})
        self.assertTrue(all(v["source"]=="checkpoint" for v in result[0]["variants"].values()))
        self.assertTrue(all(call.kwargs["temperature"]==0.0 for call in model.generate.call_args_list))
    def test_confirmation_skips_all(self):
        model=Mock()
        rows=execute(cases=[("ambiguous",["Pythonに興味がある"])],generator=model)
        self.assertEqual(rows[0]["action"],"ASK_CONFIRMATION")
        model.generate.assert_not_called()
    def test_no_fake_generation(self):
        rows=execute(cases=[("simple",["LLMを勉強したい"])])
        self.assertTrue(all(v["text"] is None for v in rows[0]["variants"].values()))
    def test_scenario_count(self):
        self.assertEqual(len(SCENARIOS),7)

if __name__=="__main__":
    unittest.main()

import unittest
from types import SimpleNamespace
from unittest.mock import patch
from context_robustness_diagnostics_v09725 import make_prompts,run

class Tokenizer:
    def encode(self,text,add_bos=False):return list(text)
class ContextRobustnessTests(unittest.TestCase):
    def test_six_conditions(self):
        prompts=make_prompts()
        self.assertEqual(len(prompts),6)
        self.assertTrue(all("あなたは誰ですか" in prompts[k] for k in list(prompts)[:5]))
        self.assertIn("名前を教えてください",prompts["F_PARAPHRASE"])
    def test_history_is_dialogue_not_inline(self):
        p=make_prompts()["D_QA_HISTORY"]
        self.assertIn("こんにちは",p)
        self.assertIn("AI: ",p)
    def test_same_decoding(self):
        calls=[]
        def generator(**kwargs):
            calls.append(kwargs)
            return SimpleNamespace(text="長門有希。",token_count=5,
                                   mean_confidence=.98,min_confidence=.92)
        result=run(None,Tokenizer(),generator)
        self.assertEqual(len(calls),6)
        self.assertEqual({x["temperature"] for x in calls},{0.0})
        self.assertEqual({x["seed"] for x in calls},{42})
        self.assertEqual(sum(x["identity_exact"] for x in result["results"].values()),6)
        self.assertEqual(result["benchmark_type"],"CONTROLLED_PROBES_NOT_HELD_OUT")
        self.assertIsNone(result["selected"])
if __name__=="__main__":unittest.main()

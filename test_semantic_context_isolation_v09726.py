import unittest
from types import SimpleNamespace
from semantic_context_isolation_v09726 import prompts,audit

class DummyTokenizer:
    def encode(self,text,add_bos=False):
        return ([0] if add_bos else [])+[ord(c) for c in text]

class IsolationTests(unittest.TestCase):
    def test_seven_prompts(self):
        p=prompts()
        self.assertEqual(len(p),7)
        self.assertTrue(all("あなたは誰ですか" in s for s in p.values()))
        self.assertIn("黒耳",p["D_ALIAS"])
        self.assertIn("会話対象:",p["F_SEMANTIC_SYNTAX"])
    def test_forced_history_is_not_pruned(self):
        p=prompts()
        g=p["G_FORCED_QA_HISTORY"]
        self.assertIn("人: こんにちは\nAI: こんにちは。\n人: あなたは誰ですか\nAI: ",g)
        self.assertGreater(len(g),len(p["A_BASELINE"]))
    def test_seven_calls_frozen_parameters(self):
        calls=[]
        def generate(**kwargs):
            calls.append(kwargs)
            return SimpleNamespace(text="長門有希。",token_count=5,
                                   mean_confidence=.98,min_confidence=.92)
        result=audit(None,DummyTokenizer(),generate)
        self.assertEqual(len(calls),7)
        self.assertEqual({c["temperature"] for c in calls},{0.0})
        self.assertEqual({c["seed"] for c in calls},{42})
        self.assertTrue(result["forced_history_verified"])
        self.assertTrue(all(x["identity_exact"] for x in result["trials"].values()))
        self.assertFalse(result["train_ready"])
if __name__=="__main__":unittest.main()

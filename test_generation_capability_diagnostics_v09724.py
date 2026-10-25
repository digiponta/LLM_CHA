import unittest
from types import SimpleNamespace
from unittest.mock import patch
from generation_capability_diagnostics_v09724 import tokenizer_audit,run

class DummyTokenizer:
    def encode(self,text,add_bos=False):
        return ([0] if add_bos else [])+[ord(x) for x in text]
    def decode(self,ids,skip_special_tokens=True):
        return "".join(chr(x) for x in ids if x>0)

class CapabilityTests(unittest.TestCase):
    def test_roundtrip(self):
        out=tokenizer_audit(DummyTokenizer(),["黒耳を飲んだ","満足した"])
        self.assertTrue(all(x["exact"] for x in out))
    def test_three_generations_same_parameters(self):
        calls=[]
        def generate(**kwargs):
            calls.append(kwargs)
            return SimpleNamespace(text="長門有希。",token_count=5,
                                   min_confidence=.7,mean_confidence=.8)
        result=run(None,DummyTokenizer(),generate)
        self.assertEqual(len(calls),3)
        self.assertEqual(set(k["seed"] for k in calls),{42})
        self.assertEqual(set(k["temperature"] for k in calls),{0.0})
        self.assertEqual(len(result["generation"]),3)
        self.assertFalse(result["training_format_verified"])
        self.assertFalse(result["train_ready"])
    def test_prompt_load_increases(self):
        def generate(**kwargs):
            return SimpleNamespace(text="長門有希。",token_count=5,
                                   min_confidence=.7,mean_confidence=.8)
        r=run(None,DummyTokenizer(),generate)
        a=r["generation"]["A_CANONICAL"]["prompt_tokens"]
        b=r["generation"]["B_SHORT_CONTEXT"]["prompt_tokens"]
        c=r["generation"]["C_LONG_CONTEXT"]["prompt_tokens"]
        self.assertLess(a,b)
        self.assertLess(b,c)
if __name__=="__main__":unittest.main()

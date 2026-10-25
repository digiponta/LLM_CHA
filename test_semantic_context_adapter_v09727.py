import unittest
from types import SimpleNamespace
from semantic_context_adapter_v09727 import alias_for,prompt_variants,audit

STATE={"entity":"ブラックベリー ヨーグルト フラペチーノ® 黒耳 ver.",
       "attributes":{"acidity":{"provenance":"USER_REPORTED"},
                     "sweetness":{"provenance":"USER_REPORTED"},
                     "chocolate":{"provenance":"USER_REPORTED"}}}
class Tok:
    def encode(self,text,add_bos=False):return list(text)
class AdapterTests(unittest.TestCase):
    def test_alias(self):
        self.assertEqual(alias_for(STATE),"黒耳")
    def test_five_formats(self):
        p=prompt_variants(STATE,"その体験は？")
        self.assertEqual(len(p),5)
        self.assertIn("会話対象:",p["A_INLINE"])
        self.assertIn("人: 黒耳を飲んだ\nAI:",p["B_DIALOGUE"])
        self.assertNotIn("ブラックベリー",str(p))
        self.assertIn("酸味",p["D_RETRIEVED"])
    def test_repeated_generation_fixed(self):
        calls=[]
        def generate(**kw):
            calls.append(kw)
            return SimpleNamespace(text="そう。",token_count=2,
                                   mean_confidence=.9,min_confidence=.7)
        r=audit(STATE,None,Tok(),generate)
        self.assertEqual(len(calls),5)
        self.assertEqual({x["temperature"] for x in calls},{0.0})
        self.assertEqual({x["seed"] for x in calls},{42})
        self.assertFalse(r["train_ready"])
        self.assertIsNone(r["selected"])
    def test_empty_rejected(self):
        self.assertEqual(audit({},None,Tok(),lambda **kw:None)["status"],"NO_SEMANTIC_STATE")
if __name__=="__main__":unittest.main()

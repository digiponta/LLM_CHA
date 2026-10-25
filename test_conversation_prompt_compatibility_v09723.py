import unittest
from types import SimpleNamespace
from conversation_prompt_compatibility_v09723 import compare,natural_context,prompts

STATE={"status":"CLOSED","entity":"ブラックベリー ヨーグルト フラペチーノ® 黒耳 ver.",
"event":"consumption","attributes":{"acidity":{"provenance":"USER_REPORTED"},
"sweetness":{"provenance":"USER_REPORTED"},
"chocolate":{"provenance":"USER_REPORTED"}},"evaluation":{"value":"満足した","provenance":"USER_REPORTED"}}
PAGE="ビバレッジ\nブラックベリー ヨーグルト フラペチーノ® 黒耳 ver.\nビバレッジ一覧へ"
class PromptCompatibilityTests(unittest.TestCase):
    def test_five_calls_same_decoding(self):
        calls=[]
        def generate(**kwargs):
            calls.append(kwargs)
            return SimpleNamespace(text="そう。",token_count=2)
        r=compare("その体験をどう思う？",STATE,PAGE,None,None,generate)
        self.assertEqual(len(calls),5)
        self.assertEqual(len(r["trials"]),5)
        self.assertEqual({c["seed"] for c in calls},{42})
        self.assertEqual({c["temperature"] for c in calls},{0.0})
        self.assertIsNone(r["selected"])
    def test_natural_context_preserves_attribution(self):
        s=natural_context(STATE)
        self.assertIn("ユーザーは",s)
        self.assertIn("未検証",s)
        self.assertIn("満足した",s)
    def test_dialogue_contains_question(self):
        p=prompts("どう思う？",STATE,PAGE)
        self.assertIn("人: どう思う？",p["D_DIALOGUE_RECONSTRUCTION"])
    def test_empty_state(self):
        self.assertEqual(compare("質問",{},PAGE,None,None,lambda **kw:None)["status"],"NO_SEMANTIC_STATE")
if __name__=="__main__": unittest.main()

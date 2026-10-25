import unittest
from types import SimpleNamespace
from conversation_semantic_generation_v09722 import compare_prompts,semantic_text,evidence_text
STATE={"status":"CLOSED","entity":"ブラックベリー ヨーグルト フラペチーノ® 黒耳 ver.",
       "event":"consumption","attributes":{"acidity":{"provenance":"USER_REPORTED"}},
       "evaluation":{"value":"満足した","provenance":"USER_REPORTED"}}
PAGE="""ビバレッジ
ブラックベリー ヨーグルト フラペチーノ® 黒耳 ver.
ビバレッジ一覧へ
フード
チーズケーキ
フード一覧へ"""
class AblationTests(unittest.TestCase):
    def test_three_real_calls_same_sampling(self):
        calls=[]
        def generate(**kw):
            calls.append(kw)
            return SimpleNamespace(text="長門有希。",token_count=4)
        report=compare_prompts("どう思う？",STATE,PAGE,object(),object(),generate)
        self.assertEqual(len(calls),3)
        self.assertEqual(list(report["trials"]),["A_BASELINE","B_SEMANTIC","C_EVIDENCE_SEMANTIC"])
        self.assertTrue(all(x["temperature"]==0 and x["seed"]==42 for x in calls))
        self.assertFalse(report["train_ready"])
        self.assertIsNone(report["selected"])
    def test_provenance_in_prompt(self):
        def generate(**kw):
            if "外部ページ根拠" in kw["prompt"]:
                self.assertIn("未検証",kw["prompt"])
            return SimpleNamespace(text="",token_count=0)
        compare_prompts("味は？",STATE,PAGE,None,None,generate)
    def test_empty_state_never_generate(self):
        def never(**kwargs):
            raise AssertionError("should not generate")
        report=compare_prompts("どう思う？",{"status":"EMPTY"},PAGE,None,None,never)
        self.assertEqual(report["status"],"NO_SEMANTIC_STATE")
    def test_semantic_source_separation(self):
        self.assertIn("ユーザー報告",semantic_text(STATE))
        self.assertIn("未検証",evidence_text(STATE,PAGE))
if __name__=="__main__":unittest.main()

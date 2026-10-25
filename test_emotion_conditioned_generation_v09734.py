import unittest
from types import SimpleNamespace
from emotion_conditioned_generation_v09734 import compare,check_response,make_prompt
from emotion_aware_dialogue_v09733 import detect

class EmotionConditionalTests(unittest.TestCase):
    def test_prompt_semantic_fields(self):
        p=make_prompt("今日は楽しかった",detect("今日は楽しかった"))
        self.assertIn("[EMOTION=ENJOYMENT]",p)
        self.assertIn("[RESPONSE_STRATEGY=SHARE_JOY]",p)
        self.assertTrue(p.endswith("AI: "))
    def test_wrong_emotion_rejected(self):
        ok,reason=check_response("それは残念だったね。",detect("今日は楽しかった"))
        self.assertFalse(ok)
        self.assertEqual(reason,"emotion-contradiction")
    def test_negation_sadness_rejected(self):
        self.assertFalse(check_response("悲しかったんだね。",detect("悲しくないよ"))[0])
    def test_acceptable_result_not_autoselected(self):
        prompts=[]
        def generator(**kwargs):
            prompts.append(kwargs["prompt"])
            return SimpleNamespace(text="楽しかったんだね。良かった。")
        result=compare("今日は楽しかった",object(),object(),generator)
        self.assertEqual(len(prompts),2)
        self.assertTrue(result["conditioned_gate_pass"])
        self.assertEqual(result["selected_route"],"DETERMINISTIC_EMOTION_BASELINE")
        self.assertTrue(result["manual_review_required"])
    def test_abstain(self):
        self.assertEqual(compare("これは何ですか",None,None,None)["status"],"ABSTAIN")
if __name__=="__main__":unittest.main()

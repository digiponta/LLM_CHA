import unittest
from types import SimpleNamespace
from train_emotion_factorial_v09738 import prompt,examples,ARMS
from evaluate_emotion_factorial_v09738 import evaluate

class FactorialTests(unittest.TestCase):
    def test_prompt_isolation(self):
        a={arm:prompt("今日は楽しかった","POSITIVE","SHARE_JOY",arm) for arm in ARMS}
        self.assertNotIn("[EMOTION=",a["plain"])
        self.assertNotIn("[RESPONSE_STRATEGY=",a["plain"])
        self.assertIn("[EMOTION=POSITIVE]",a["emotion"])
        self.assertNotIn("[RESPONSE_STRATEGY=",a["emotion"])
        self.assertNotIn("[EMOTION=",a["strategy"])
        self.assertIn("[RESPONSE_STRATEGY=SHARE_JOY]",a["strategy"])
        self.assertIn("[EMOTION=POSITIVE]",a["both"])
        self.assertIn("[RESPONSE_STRATEGY=SHARE_JOY]",a["both"])
    def test_protected_replay_same_across_arms(self):
        data={"train":[{"input":"今日は楽しかった","target":"良かったね。",
            "semantic":{"emotion":"POSITIVE","response_strategy":"SHARE_JOY"}}]}
        replay={arm:examples(data,3,arm)[1:] for arm in ARMS}
        self.assertTrue(all(replay[a]==replay["plain"] for a in ARMS))
    def test_four_arm_evaluation(self):
        cases=[{"id":"x","source":"holdout","emotion":"POSITIVE",
           "strategy":"SHARE_JOY","input":"嬉しい","reference":"それは良かったね。"}]
        def fake(m,t,p,**kwargs):return SimpleNamespace(text="それは良かったね。")
        r=evaluate({a:object() for a in ARMS},object(),cases,generator=fake)
        self.assertEqual(len(r["rows"][0]["outputs"]),4)
        self.assertEqual(r["summary"]["both"]["holdout_exact"],1)
if __name__=="__main__":unittest.main()

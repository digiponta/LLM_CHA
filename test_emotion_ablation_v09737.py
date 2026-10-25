import unittest
from evaluate_emotion_ablation_v09737 import prompts,diversity,evaluate

class AblationTests(unittest.TestCase):
    def test_independent_swaps(self):
        p=prompts("今日は楽しかった","ENJOYMENT","SHARE_JOY")
        self.assertIn("[EMOTION=ENJOYMENT]",p["correct"])
        self.assertIn("[RESPONSE_STRATEGY=SHARE_JOY]",p["correct"])
        self.assertIn("[EMOTION=DISAPPOINTMENT]",p["emotion_only_swapped"])
        self.assertIn("[RESPONSE_STRATEGY=SHARE_JOY]",p["emotion_only_swapped"])
        self.assertIn("[EMOTION=ENJOYMENT]",p["strategy_only_swapped"])
        self.assertIn("[RESPONSE_STRATEGY=ACKNOWLEDGE_DISAPPOINTMENT]",p["strategy_only_swapped"])
    def test_diversity(self):
        d=diversity(["A","B","A"])
        self.assertEqual(d["unique"],2)
        self.assertEqual(d["top_count"],2)
        self.assertEqual(d["total"],3)
    def test_four_generation_variants(self):
        seen=[]
        def runner(model,tok,prompt,seed):
            seen.append(prompt)
            return {"text":prompt.splitlines()[0],"tokens":1}
        cases=[{"id":"test","source":"holdout","input":"今日は楽しかった",
                "emotion":"ENJOYMENT","strategy":"SHARE_JOY","reference":"期待文字列"}]
        r=evaluate(None,None,cases,runner=runner)
        self.assertEqual(len(seen),4)
        self.assertEqual(r["case_count"],1)
        self.assertEqual(r["change_summary"]["emotion_only_swapped"],1)
        self.assertEqual(r["change_summary"]["strategy_only_swapped"],0)
        self.assertEqual(r["summary"]["correct"]["holdout_exact"],0)
    def test_empty_diversity(self):
        self.assertEqual(diversity([])["top_rate"],0)
if __name__=="__main__":unittest.main()

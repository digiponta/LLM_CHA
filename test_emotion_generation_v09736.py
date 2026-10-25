import unittest
from types import SimpleNamespace
from evaluate_emotion_generation_v09736 import build_cases,evaluate,SWAP

class GenerationEvaluationTests(unittest.TestCase):
    def test_cases(self):
        cases=build_cases()
        self.assertEqual(len(cases),37)
        self.assertEqual(sum(r["source"]=="holdout" for r in cases),30)
        self.assertEqual(sum(r["source"]=="challenge" for r in cases),7)
        self.assertEqual(len({r["id"] for r in cases}),37)
    def test_swaps(self):
        self.assertEqual(SWAP["POSITIVE"],"DISAPPOINTMENT")
        self.assertEqual(SWAP["NEGATED_SADNESS"],"SADNESS")
    def test_all_five_controls(self):
        calls=[]
        def mock(model,tok,prompt,seed):
            calls.append((prompt,seed))
            return {"text":"それは良かったね。","tokens":6,
                    "mean_confidence":0.9,"min_confidence":0.6}
        one=[{"id":"h1","source":"holdout","input":"今日は楽しかった",
              "emotion":"ENJOYMENT","strategy":"SHARE_JOY",
              "reference":"それは良かったね。"}]
        result=evaluate({"baseline":object(),"daily":object(),
                         "conditioned":object()},object(),one,runner=mock)
        self.assertEqual(len(calls),5)
        self.assertEqual(len(result["rows"]),1)
        self.assertEqual(result["summary"]["conditioned_correct"]["holdout_exact"],1)
        self.assertNotEqual(calls[3][0],calls[4][0])
        self.assertEqual({s for _,s in calls},{42})
    def test_eval_only(self):
        cases=build_cases()
        self.assertTrue(all(r["reference"] is None for r in cases if r["source"]=="challenge"))
if __name__=="__main__":unittest.main()

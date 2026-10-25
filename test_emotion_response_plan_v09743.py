import unittest
from types import SimpleNamespace
from emotion_response_plan_v09743 import plan
from evaluate_emotion_response_plan_v09743 import evaluate

class ResponsePlanTests(unittest.TestCase):
    def test_sadness_primary(self):
        p=plan("嬉しいけれど悲しい")
        self.assertEqual(p.primary_emotion,"SADNESS")
        self.assertEqual(p.primary_emotion_value,-0.75)
        self.assertEqual(p.overall_emotion_value,-0.25)
        self.assertEqual(p.secondary_emotions,("JOY",))
    def test_reverse(self):
        p=plan("悲しいけれど嬉しい")
        self.assertEqual((p.primary_emotion,p.overall_emotion_value),("JOY",0.25))
    def test_deduplicate(self):
        p=plan("嬉しいけれど悲しいけれど嬉しい")
        self.assertEqual(p.secondary_emotions,("SADNESS",))
    def test_fatigue(self):
        p=plan("楽しかったけど疲れた")
        self.assertEqual(p.primary_emotion,"FATIGUE")
        self.assertIn("疲れた",p.response)
    def test_explicit_negation(self):
        p=plan("悲しくない。むしろ嬉しい。")
        self.assertEqual(p.primary_emotion_value,0.75)
        self.assertEqual(p.secondary_emotions,())
    def test_unknown(self):
        self.assertIsNone(plan("量子力学について教えて"))
    def test_no_mutation(self):
        p=plan("嬉しいけれど悲しい")
        self.assertFalse(p.train_ready or p.auto_promote or p.persisted)
    def test_evaluation(self):
        def stub(model,tok,prompt,**kw):return SimpleNamespace(text="sample")
        r=evaluate(["嬉しいけれど悲しい"],object(),object(),runner=stub)
        self.assertEqual(r["count"],1)
        self.assertEqual(r["rows"][0]["combined_sft_generated"],"sample")
if __name__=="__main__":unittest.main()

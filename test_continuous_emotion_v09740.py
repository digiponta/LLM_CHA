import unittest
from continuous_emotion_semantics_v09740 import detect_affect,safe_response

class ContinuousEmotionTests(unittest.TestCase):
    def test_negated_sadness_positive_neutral(self):
        a=detect_affect("悲しくないよ")
        self.assertEqual(a.axis,"SADNESS_JOY")
        self.assertEqual(a.value,0.25)
        self.assertTrue(a.negated)
        self.assertFalse(a.inferred_opposite)
        self.assertEqual(a.state,"POSITIVE_LEANING_NEUTRAL")
        self.assertEqual(safe_response(a),"悲しいわけではないんだね。")
    def test_negated_joy_negative_neutral(self):
        a=detect_affect("嬉しくない")
        self.assertEqual(a.value,-0.25)
        self.assertEqual(a.state,"NEGATIVE_LEANING_NEUTRAL")
    def test_other_explicit_wins(self):
        a=detect_affect("悲しくない。むしろ嬉しい。")
        self.assertEqual(a.value,0.75)
        self.assertEqual(a.source_emotion,"JOY")
        self.assertFalse(a.inferred_opposite)
    def test_negated_fear(self):
        a=detect_affect("不安ではない")
        self.assertEqual((a.axis,a.value),("ANXIETY_CALM",0.25))
        self.assertEqual(safe_response(a),"不安ではないんだね。")
    def test_opposite_coexists(self):
        a=detect_affect("嬉しいけれど悲しい")
        self.assertEqual(a.state,"MIXED")
        self.assertEqual(a.value,0.0)
    def test_unhandled(self):
        self.assertIsNone(detect_affect("量子力学について教えて"))
    def test_ephemeral(self):
        d=detect_affect("寂しくない").snapshot()
        self.assertFalse(d["train_ready"])
        self.assertFalse(d["auto_promote"])
        self.assertFalse(d["persisted"])
    def test_independent_axis_refused(self):
        self.assertIsNone(detect_affect("悲しくないし、不安ではない"))
if __name__=="__main__":unittest.main()

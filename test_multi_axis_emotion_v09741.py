import unittest
from multi_axis_emotion_v09741 import detect_multi,safe_response

class MultiAxisTests(unittest.TestCase):
    def test_enjoyment_and_fatigue(self):
        s=detect_multi("楽しかったけど疲れた")
        self.assertEqual(s.state,"MIXED")
        self.assertEqual(s.relation,"CONTRAST")
        self.assertEqual(s.axes["SADNESS_JOY"],0.75)
        self.assertEqual(s.axes["FATIGUE_ENERGY"],-0.75)
        self.assertEqual(len(s.components),2)
        self.assertIn("疲れた",safe_response(s))
    def test_two_independent_negations(self):
        s=detect_multi("悲しくないし、不安ではない")
        self.assertEqual(s.state,"MULTI_AXIS_NEUTRAL")
        self.assertEqual(s.axes,{"SADNESS_JOY":0.25,"ANXIETY_CALM":0.25})
        self.assertEqual(safe_response(s),"悲しくも不安でもないんだね。")
    def test_opposite_explicit_retained(self):
        s=detect_multi("嬉しいけれど悲しい")
        self.assertEqual(s.state,"MIXED")
        self.assertIsNone(s.axes["SADNESS_JOY"])
        self.assertEqual([p.emotion for p in s.components],["JOY","SADNESS"])
    def test_negation_and_explicit_override(self):
        s=detect_multi("悲しくない。むしろ嬉しい。")
        self.assertEqual(len(s.components),2)
        self.assertEqual(s.axes["SADNESS_JOY"],0.5)
        self.assertFalse(s.persisted)
    def test_negated_joy(self):
        s=detect_multi("嬉しくない")
        self.assertEqual(s.axes["SADNESS_JOY"],-0.25)
        self.assertEqual(safe_response(s),"嬉しい気持ちではないんだね。")
    def test_no_auto_promotion(self):
        s=detect_multi("楽しかったけど疲れた").snapshot()
        self.assertFalse(s["train_ready"])
        self.assertFalse(s["auto_promote"])
        self.assertFalse(s["persisted"])
    def test_unknown(self):
        self.assertIsNone(detect_multi("量子力学について教えて"))
if __name__=="__main__":unittest.main()

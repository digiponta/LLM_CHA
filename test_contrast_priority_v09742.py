import unittest
from contrast_priority_emotion_v09742 import detect_priority,safe_response

class ContrastPriorityTests(unittest.TestCase):
    def test_sadness_post_contrast(self):
        s=detect_priority("嬉しいけれど悲しい")
        self.assertEqual(s.state,"SADNESS_LEANING_NEUTRAL")
        self.assertEqual(s.axes["SADNESS_JOY"],-0.25)
        self.assertEqual(s.primary_emotion,"SADNESS")
        self.assertIn("JOY",s.secondary_emotions)
        self.assertEqual(len(s.components),2)
    def test_joy_post_contrast(self):
        s=detect_priority("悲しいけれど嬉しい")
        self.assertEqual(s.axes["SADNESS_JOY"],0.25)
        self.assertEqual(s.primary_emotion,"JOY")
    def test_fatigue_post_contrast(self):
        s=detect_priority("楽しかったけど疲れた")
        self.assertEqual(s.primary_emotion,"FATIGUE")
        self.assertEqual(s.axes["FATIGUE_ENERGY"],-0.75)
        self.assertIn("疲れた",safe_response(s))
    def test_explicit_after_negation(self):
        s=detect_priority("悲しくない。むしろ嬉しい。")
        self.assertEqual(s.state,"POSITIVE_EXPLICIT")
        self.assertEqual(s.axes["SADNESS_JOY"],0.75)
        self.assertEqual(s.priority_rule,"EXPLICIT_AFTER_NEGATION")
    def test_not_contrast_without_second_emotion(self):
        s=detect_priority("悲しいけれど、どうすればいい？")
        self.assertEqual(s.priority_rule,"NONE")
    def test_existing_plain_negation(self):
        s=detect_priority("悲しくない")
        self.assertEqual(s.axes["SADNESS_JOY"],0.25)
    def test_safe_no_mutation(self):
        s=detect_priority("嬉しいけれど悲しい")
        self.assertFalse(s.train_ready)
        self.assertFalse(s.persisted)
        self.assertFalse(s.auto_promote)
if __name__=="__main__":unittest.main()

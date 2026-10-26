import unittest
from semantic_dialogue_transition_v09773 import parse_transition
from semantic_dialogue_state_v09770 import extract_reason
F=extract_reason("きらきらしてるところが心地よい","スファレライト")
class Tests(unittest.TestCase):
    def test_reject(self):
        self.assertEqual(parse_transition("そうじゃない","スファレライト",F).intent,"reject_previous")
    def test_correction(self):
        x=parse_transition("きらきらより色が好き","スファレライト",F)
        self.assertEqual((x.intent,x.quality),("correct_preference","色"))
    def test_topic(self):
        self.assertEqual(parse_transition("ところでダイヤモンドは？","スファレライト",F).topic,"ダイヤモンド")
    def test_no_context_correction(self):
        self.assertIsNone(parse_transition("きらきらより色が好き","スファレライト",None))
    def test_not_fact(self):
        self.assertIsNone(parse_transition("屈折率は？","スファレライト",F))
if __name__=="__main__":
    unittest.main()

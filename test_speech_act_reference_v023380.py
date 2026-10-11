import unittest
from speech_act_reference_v023380 import route_speech_act

class SpeechActReferenceTests(unittest.TestCase):
    def test_thanks(self):
        x=route_speech_act("ありがとう")
        self.assertEqual(x["kind"],"ACKNOWLEDGEMENT")
        self.assertEqual(x["answer"],"どういたしまして。")
    def test_polite_thanks(self):
        self.assertEqual(route_speech_act("ありがとうございます！")["kind"],"ACKNOWLEDGEMENT")
    def test_ambiguous_experiment(self):
        x=route_speech_act("あの実験の続き")
        self.assertEqual(x["kind"],"REFERENCE_CLARIFY")
        self.assertIn("どの実験",x["answer"])
    def test_followup_does_not_invent_fact(self):
        x=route_speech_act("もう少し詳しく")
        self.assertEqual(x["kind"],"FOLLOWUP_CLARIFY")
        self.assertIn("どの話題",x["answer"])
    def test_knowledge_unchanged(self):
        self.assertIsNone(route_speech_act("宇宙とは"))
        self.assertIsNone(route_speech_act("GPUとは"))
    def test_slash_command_unchanged(self):
        self.assertIsNone(route_speech_act("/truth GPU"))
    def test_nonmatching_references_remain_unchanged(self):
        self.assertIsNone(route_speech_act("実験装置の説明をしてください"))
if __name__=="__main__":unittest.main()

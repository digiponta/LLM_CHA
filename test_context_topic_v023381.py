import unittest
from speech_act_reference_v023380 import extract_topic,route_speech_act
from extended_chat_runtime_v023378 import evaluate,CASES

class ContextAndCompatibilityTests(unittest.TestCase):
    def test_extract_topic_japanese(self):
        self.assertEqual(extract_topic("宇宙について教えて"),"宇宙")
    def test_extract_topic_ascii(self):
        self.assertEqual(extract_topic("GPUとは"),"GPU")
    def test_no_topic_from_greeting(self):
        self.assertIsNone(extract_topic("こんにちは"))
    def test_followup_known_topic_routes_through_truth(self):
        r=route_speech_act("もう少し詳しく",previous_user="宇宙")
        self.assertEqual(r["kind"],"FOLLOWUP_TOPIC_ROUTE")
        self.assertEqual(r["routed_query"],"宇宙とは")
    def test_followup_without_topic_requests_clarification(self):
        r=route_speech_act("もう少し詳しく")
        self.assertEqual(r["kind"],"FOLLOWUP_CLARIFY")
    def test_thanks_and_reference_still_safe(self):
        self.assertEqual(route_speech_act("ありがとう")["kind"],"ACKNOWLEDGEMENT")
        self.assertEqual(route_speech_act("あの実験の続き")["kind"],"REFERENCE_CLARIFY")
    def test_reference_marker_compatibility(self):
        cases=(CASES[4],)
        r=evaluate("You> AI> どの実験・話題の続きでしょうか？\n[speech-act=REFERENCE_CLARIFY]\n",0,cases)
        self.assertTrue(r["acceptance_pass"])
if __name__=="__main__":unittest.main()

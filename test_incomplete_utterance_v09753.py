import unittest
from incomplete_utterance_v09753 import detect
from definition_intent_v09752 import resolve

class IncompleteUtteranceTests(unittest.TestCase):
    def test_topic_wa(self):
        p=detect("満足は")
        self.assertEqual(p.topic,"満足")
        self.assertIn("何を知りたい",p.response)
    def test_topic_mo(self):
        self.assertEqual(detect("コーヒーも").particle,"も")
    def test_topic_wo(self):
        self.assertEqual(detect("ケーキを").particle,"を")
    def test_definition_still_search(self):
        self.assertIsNone(detect("満足とは"))
        self.assertIsNotNone(resolve("満足とは"))
    def test_complete_sentence_not_intercepted(self):
        for s in ("満足は大切","満足はできた","満足した","満足","美味しかった","本を買った"):
            self.assertIsNone(detect(s),s)
    def test_question_not_intercepted(self):
        self.assertIsNone(detect("満足は？"))
    def test_quoted_not_intercepted(self):
        self.assertIsNone(detect("「満足は」"))
    def test_command_not_intercepted(self):
        self.assertIsNone(detect("/exit"))
    def test_no_write_or_training(self):
        p=detect("満足は")
        self.assertFalse(p.train_ready or p.auto_promote or p.persisted)
if __name__=="__main__":unittest.main()

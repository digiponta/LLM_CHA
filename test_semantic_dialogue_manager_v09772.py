import unittest
from semantic_dialogue_manager_v09772 import SemanticDialogueManager

class DialogueManagerTests(unittest.TestCase):
    def test_full_scenario(self):
        m=SemanticDialogueManager()
        r=m.handle("私は、スファレライトが好きです。", "スファレライト")
        self.assertEqual(r.route,"TOPIC_PREFERENCE_ACK")
        self.assertEqual(r.frame.intent,"express_preference")
        r=m.handle("きらきらしてるところが心地よい","スファレライト")
        self.assertEqual(r.frame.intent,"explain_preference")
        self.assertEqual(r.frame.truth_state,"USER_REPORTED")
        r=m.handle("そうだよ","スファレライト")
        self.assertEqual(r.route,"SEMANTIC_DIALOGUE_AGREEMENT")
        self.assertIsNone(m.handle("そうだよ","スファレライト"))
    def test_fact_question_not_consumed(self):
        m=SemanticDialogueManager()
        m.handle("私は、スファレライトが好きです。","スファレライト")
        self.assertIsNone(m.handle("屈折率は？","スファレライト"))
        self.assertIsNone(m.handle("きらきらしてるところが心地よい","スファレライト"))
    def test_no_stale_agreement(self):
        m=SemanticDialogueManager()
        m.handle("スファレライトが好きです")
        m.handle("きれいだから")
        self.assertIsNone(m.handle("化学組成は？"))
        self.assertIsNone(m.handle("そうだよ"))
    def test_no_pending_without_preference(self):
        self.assertIsNone(SemanticDialogueManager().handle("そうだよ"))
    def test_commands_do_not_reply(self):
        self.assertIsNone(SemanticDialogueManager().handle("/sleep"))
if __name__=="__main__":
    unittest.main()

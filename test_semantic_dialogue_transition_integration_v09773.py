import unittest
from semantic_dialogue_manager_v09772 import SemanticDialogueManager

class TransitionIntegrationTests(unittest.TestCase):
    def prepared(self):
        m=SemanticDialogueManager()
        m.handle("私は、スファレライトが好きです。","スファレライト")
        m.handle("きらきらしてるところが心地よい","スファレライト")
        return m
    def test_reject(self):
        m=self.prepared()
        self.assertEqual(m.handle("そうじゃない","スファレライト").route,"SEMANTIC_DIALOGUE_REJECTION")
        confirmation=m.handle("そうだよ","スファレライト")
        self.assertEqual(confirmation.route,"SEMANTIC_DIALOGUE_CLARIFICATION")
        self.assertEqual(m.journal.latest().event,"clarification_acknowledged")
        self.assertNotIn("スファレライト",m.journal.focus)
    def test_correction(self):
        m=self.prepared()
        r=m.handle("きらきらより色が好き","スファレライト")
        self.assertEqual(r.route,"SEMANTIC_DIALOGUE_CORRECTION")
        self.assertIn("色",r.reply)
    def test_switch(self):
        m=self.prepared()
        r=m.handle("ところでダイヤモンドは？","スファレライト")
        self.assertEqual(r.next_topic,"ダイヤモンド")
        self.assertEqual(r.route,"SEMANTIC_DIALOGUE_TOPIC_SWITCH")
    def test_evidence_question_unhandled(self):
        m=self.prepared()
        self.assertIsNone(m.handle("屈折率は？","スファレライト"))
if __name__=="__main__":
    unittest.main()

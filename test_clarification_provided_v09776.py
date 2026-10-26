import unittest
from semantic_dialogue_manager_v09772 import SemanticDialogueManager
class ClarificationProvidedTests(unittest.TestCase):
    def setup_dialogue(self):
        m=SemanticDialogueManager()
        m.handle("私は、スファレライトが好きです。","スファレライト")
        m.handle("きらきらしてるところが心地よい","スファレライト")
        m.handle("そうじゃない","スファレライト")
        return m
    def test_after_ack(self):
        m=self.setup_dialogue()
        m.handle("そうだよ","スファレライト")
        r=m.handle("本当は色の変化が好きなんだ","スファレライト")
        self.assertEqual(r.route,"SEMANTIC_DIALOGUE_CLARIFICATION_PROVIDED")
        e=m.journal.latest()
        self.assertEqual((e.event,e.updated_quality),("clarification_provided","色の変化"))
        self.assertEqual(m.journal.focus["スファレライト"],"色の変化")
    def test_direct_clarification(self):
        m=self.setup_dialogue()
        self.assertEqual(m.handle("本当は色の変化が好きなんだ","スファレライト").route,"SEMANTIC_DIALOGUE_CLARIFICATION_PROVIDED")
    def test_no_context(self):
        self.assertIsNone(SemanticDialogueManager().handle("本当は色の変化が好きなんだ"))
    def test_interruption(self):
        m=self.setup_dialogue()
        m.handle("そうだよ","スファレライト")
        self.assertIsNone(m.handle("屈折率は？","スファレライト"))
        self.assertIsNone(m.handle("本当は色の変化が好きなんだ","スファレライト"))
    def test_not_reinstate_rejected(self):
        m=self.setup_dialogue()
        m.handle("そうだよ","スファレライト")
        m.handle("本当は色の変化が好きなんだ","スファレライト")
        self.assertNotEqual(m.journal.focus["スファレライト"],"sparkling")
if __name__=="__main__":unittest.main()

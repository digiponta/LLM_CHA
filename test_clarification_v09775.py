import unittest
from semantic_dialogue_manager_v09772 import SemanticDialogueManager

class ClarificationTests(unittest.TestCase):
    def prepare(self):
        manager=SemanticDialogueManager()
        manager.handle("私は、スファレライトが好きです。","スファレライト")
        manager.handle("きらきらしてるところが心地よい","スファレライト")
        self.assertEqual(manager.handle("そうじゃない","スファレライト").route,
                         "SEMANTIC_DIALOGUE_REJECTION")
        return manager
    def test_confirm_after_rejection(self):
        manager=self.prepare()
        result=manager.handle("そうだよ","スファレライト")
        self.assertEqual(result.route,"SEMANTIC_DIALOGUE_CLARIFICATION")
        self.assertIn("もう少し教えて",result.reply)
        self.assertEqual(manager.journal.latest().event,"clarification_acknowledged")
    def test_rejected_quality_stays_cleared(self):
        manager=self.prepare()
        self.assertNotIn("スファレライト",manager.journal.focus)
        manager.handle("そうだよ","スファレライト")
        self.assertNotIn("スファレライト",manager.journal.focus)
    def test_not_repeated(self):
        manager=self.prepare()
        manager.handle("そうだよ","スファレライト")
        self.assertIsNone(manager.handle("そうだよ","スファレライト"))
    def test_unrelated_clears(self):
        manager=self.prepare()
        self.assertIsNone(manager.handle("屈折率は？","スファレライト"))
        self.assertIsNone(manager.handle("そうだよ","スファレライト"))

if __name__ == "__main__":
    unittest.main()

import unittest
from types import SimpleNamespace
from semantic_dialogue_manager_v09772 import SemanticDialogueManager
from semantic_integrity_gate_v09782 import evaluate_integrity

class GateTests(unittest.TestCase):
    def test_empty_partial(self):
        self.assertEqual(evaluate_integrity(SemanticDialogueManager()).status,"PARTIAL")
    def test_valid_preference_partial(self):
        m=SemanticDialogueManager()
        m.handle("私は、スファレライトが好きです。","スファレライト")
        self.assertTrue(evaluate_integrity(m).allow_dialogue)
    def test_valid_switch(self):
        m=SemanticDialogueManager()
        r=m.handle("ところでダイヤモンドは？","スファレライト")
        self.assertEqual(evaluate_integrity(m,SimpleNamespace(active_topic=r.next_topic)).status,"ALLOW")
    def test_corrupt_focus_blocks(self):
        m=SemanticDialogueManager()
        m.handle("私は、スファレライトが好きです。","スファレライト")
        m.handle("きらきらしてるところが心地よい","スファレライト")
        m.journal.focus["スファレライト"]="色"
        self.assertFalse(evaluate_integrity(m).allow_dialogue)
    def test_topic_mismatch_blocks(self):
        m=SemanticDialogueManager()
        m.handle("ところでダイヤモンドは？","スファレライト")
        self.assertEqual(evaluate_integrity(m,SimpleNamespace(active_topic="スファレライト")).status,"BLOCK")
    def test_truncated_blocks(self):
        m=SemanticDialogueManager()
        m.journal.max_events=1
        m.journal.record("agreement","x")
        m.journal.record("agreement","x")
        self.assertEqual(evaluate_integrity(m).status,"BLOCK")
if __name__=="__main__":unittest.main()

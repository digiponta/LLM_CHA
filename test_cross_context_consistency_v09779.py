import unittest
from types import SimpleNamespace
from semantic_dialogue_manager_v09772 import SemanticDialogueManager
from cross_context_consistency_v09779 import validate_cross_context

class CrossContextTests(unittest.TestCase):
    def test_explicit_topic_switch_consistent(self):
        m=SemanticDialogueManager()
        result=m.handle("ところでダイヤモンドは？","スファレライト")
        topic=SimpleNamespace(active_topic=result.next_topic)
        r=validate_cross_context(m,topic)
        self.assertEqual(r.status,"CONSISTENT")
        self.assertIn("semantic_memory",r.not_comparable)
    def test_explicit_topic_switch_mismatch(self):
        m=SemanticDialogueManager()
        m.handle("ところでダイヤモンドは？","スファレライト")
        r=validate_cross_context(m,SimpleNamespace(active_topic="スファレライト"))
        self.assertEqual(r.status,"MISMATCH")
        self.assertIn("topic_context.active_topic",r.mismatches)
    def test_preference_only_not_comparable_topic(self):
        m=SemanticDialogueManager()
        m.handle("私は、スファレライトが好きです。","スファレライト")
        r=validate_cross_context(m,SimpleNamespace(active_topic=None))
        self.assertEqual(r.status,"NOT_COMPARABLE")
        self.assertIn("topic_context.active_topic",r.not_comparable)
    def test_truncated_replay(self):
        m=SemanticDialogueManager()
        m.journal.max_events=2
        for i in range(3):
            m.journal.record("agreement","x")
        self.assertEqual(validate_cross_context(m).status,"INCOMPLETE")
    def test_tampered_quality(self):
        m=SemanticDialogueManager()
        m.handle("私は、スファレライトが好きです。","スファレライト")
        m.handle("きらきらしてるところが心地よい","スファレライト")
        m.journal.focus["スファレライト"]="色"
        self.assertEqual(validate_cross_context(m).status,"MISMATCH")
if __name__=="__main__":
    unittest.main()

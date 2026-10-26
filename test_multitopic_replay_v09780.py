import unittest
from types import SimpleNamespace
from semantic_dialogue_manager_v09772 import SemanticDialogueManager
from cross_context_consistency_v09779 import validate_cross_context

class MultiTopicReplayTests(unittest.TestCase):
    def test_explicit_source_target(self):
        m=SemanticDialogueManager()
        m.handle("私は、スファレライトが好きです。","スファレライト")
        m.handle("きらきらしてるところが心地よい","スファレライト")
        r=m.handle("ところでダイヤモンドは？","スファレライト")
        e=m.journal.latest()
        self.assertEqual((e.source_topic,e.target_topic,e.previous_quality),("スファレライト","ダイヤモンド",None))
        self.assertEqual(m.journal.replay().active_topic,"ダイヤモンド")
        self.assertEqual(validate_cross_context(m,SimpleNamespace(active_topic=r.next_topic)).status,"CONSISTENT")
    def test_rejection_wait_state(self):
        m=SemanticDialogueManager()
        m.handle("私は、スファレライトが好きです。","スファレライト")
        m.handle("きらきらしてるところが心地よい","スファレライト")
        m.handle("そうじゃない","スファレライト")
        self.assertEqual(m.journal.replay().awaiting_clarification,"スファレライト")
        self.assertEqual(validate_cross_context(m).status,"CONSISTENT")
        m.handle("そうだよ","スファレライト")
        self.assertEqual(m.journal.replay().awaiting_new_reason,"スファレライト")
        self.assertNotIn("manager.awaiting_new_reason",validate_cross_context(m).mismatches)
    def test_reason_resolution(self):
        m=SemanticDialogueManager()
        for t in ("私は、スファレライトが好きです。","きらきらしてるところが心地よい","そうじゃない","そうだよ","本当は色の変化が好きなんだ"):
            m.handle(t,"スファレライト")
        replay=m.journal.replay()
        self.assertIsNone(replay.awaiting_clarification)
        self.assertIsNone(replay.awaiting_new_reason)
        self.assertEqual(replay.preferences["スファレライト"]["quality"],"色の変化")
    def test_interruption_cancelled(self):
        m=SemanticDialogueManager()
        for t in ("私は、スファレライトが好きです。","きらきらしてるところが心地よい","そうじゃない"):
            m.handle(t,"スファレライト")
        self.assertIsNone(m.handle("屈折率は？","スファレライト"))
        self.assertEqual(m.journal.latest().event,"clarification_cancelled")
        self.assertIsNone(m.journal.replay().awaiting_clarification)
        self.assertNotIn("manager.awaiting_clarification",validate_cross_context(m).mismatches)
    def test_topic_round_trip(self):
        m=SemanticDialogueManager()
        m.handle("私は、スファレライトが好きです。","スファレライト")
        m.handle("きらきらしてるところが心地よい","スファレライト")
        m.handle("ところでダイヤモンドは？","スファレライト")
        m.handle("ところでスファレライトは？","ダイヤモンド")
        replay=m.journal.replay()
        self.assertEqual(replay.active_topic,"スファレライト")
        self.assertEqual(replay.preferences["スファレライト"]["quality"],"sparkling")
        self.assertEqual(m.journal.latest().source_topic,"ダイヤモンド")
if __name__=="__main__":
    unittest.main()

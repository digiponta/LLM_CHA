import unittest
from semantic_dialogue_manager_v09772 import SemanticDialogueManager
from semantic_event_replay_v09777 import replay_semantic_events
from semantic_event_journal_v09774 import SemanticEventJournal

class ReplayTests(unittest.TestCase):
    def test_actual_five_events(self):
        m=SemanticDialogueManager()
        for line in ("私は、スファレライトが好きです。","きらきらしてるところが心地よい","そうじゃない","そうだよ","本当は色の変化が好きなんだ"):
            self.assertIsNotNone(m.handle(line,"スファレライト"))
        state=replay_semantic_events(m.journal.events)
        self.assertTrue(state.complete)
        self.assertEqual(state.active_topic,"スファレライト")
        self.assertEqual(state.preferences["スファレライト"]["quality"],"色の変化")
        self.assertEqual(state.rejected_qualities["スファレライト"],["sparkling"])
        self.assertEqual(state.preferences["スファレライト"]["preference"],"likes")
        self.assertEqual(m.journal.focus["スファレライト"],state.preferences["スファレライト"]["quality"])
    def test_topic_switch(self):
        j=SemanticEventJournal()
        j.record("express_preference","スファレライト")
        j.record("switch_topic","ダイヤモンド")
        self.assertEqual(replay_semantic_events(j.events).active_topic,"ダイヤモンド")
    def test_truncated_is_incomplete(self):
        j=SemanticEventJournal(max_events=2)
        for i in range(4): j.record("agreement","スファレライト")
        self.assertFalse(replay_semantic_events(j.events).complete)
    def test_empty(self):
        self.assertTrue(replay_semantic_events([]).complete)
    def test_rejected_not_reinstated(self):
        j=SemanticEventJournal()
        j.record("express_preference","スファレライト")
        j.record("explain_preference","スファレライト",updated_quality="sparkling")
        j.record("reject_previous","スファレライト",previous_quality="sparkling")
        j.record("clarification_acknowledged","スファレライト")
        self.assertIsNone(replay_semantic_events(j.events).preferences["スファレライト"]["quality"])
if __name__=="__main__":unittest.main()

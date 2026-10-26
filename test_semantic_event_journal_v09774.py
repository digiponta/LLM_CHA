import unittest
from semantic_event_journal_v09774 import SemanticEventJournal
from semantic_dialogue_manager_v09772 import SemanticDialogueManager

class JournalTests(unittest.TestCase):
    def test_correction_history(self):
        m=SemanticDialogueManager()
        m.handle("私は、スファレライトが好きです。","スファレライト")
        m.handle("きらきらしてるところが心地よい","スファレライト")
        r=m.handle("きらきらより色が好き","スファレライト")
        self.assertEqual(r.route,"SEMANTIC_DIALOGUE_CORRECTION")
        e=m.journal.latest().to_dict()
        self.assertEqual(e["event"],"correct_preference")
        self.assertEqual(e["previous_quality"],"sparkling")
        self.assertEqual(e["updated_quality"],"色")
        self.assertEqual(e["truth_state"],"USER_REPORTED")
    def test_topic_switch(self):
        m=SemanticDialogueManager()
        m.handle("ところでダイヤモンドは？","スファレライト")
        self.assertEqual(m.journal.latest().event,"switch_topic")
    def test_sequence(self):
        j=SemanticEventJournal()
        self.assertEqual(j.record("a","x").sequence,1)
        self.assertEqual(j.record("b","x").sequence,2)
    def test_bounded(self):
        j=SemanticEventJournal(max_events=2)
        for i in range(5):j.record("event","x")
        self.assertEqual(len(j.events),2)
    def test_no_storage(self):
        self.assertEqual(SemanticEventJournal().events,[])

if __name__=="__main__":
    unittest.main()

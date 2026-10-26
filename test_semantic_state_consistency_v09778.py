import unittest
from semantic_event_journal_v09774 import SemanticEventJournal
from semantic_state_consistency_v09778 import validate_semantic_consistency

class ConsistencyTests(unittest.TestCase):
    def test_consistent(self):
        j=SemanticEventJournal()
        j.record("express_preference","スファレライト")
        j.record("explain_preference","スファレライト",updated_quality="sparkling")
        self.assertEqual(validate_semantic_consistency(j,"スファレライト").status,"CONSISTENT")
    def test_tampered_runtime(self):
        j=SemanticEventJournal()
        j.record("explain_preference","スファレライト",updated_quality="sparkling")
        j.focus["スファレライト"]="色"
        r=validate_semantic_consistency(j)
        self.assertEqual(r.status,"MISMATCH")
        self.assertIn("quality_focus",r.mismatches)
    def test_topic_mismatch(self):
        j=SemanticEventJournal()
        j.record("switch_topic","ダイヤモンド")
        self.assertIn("active_topic",validate_semantic_consistency(j,"スファレライト").mismatches)
    def test_incomplete(self):
        j=SemanticEventJournal(max_events=2)
        for i in range(3): j.record("agreement","スファレライト")
        self.assertEqual(validate_semantic_consistency(j).status,"INCOMPLETE")
    def test_rejected_focus_cleared(self):
        j=SemanticEventJournal()
        j.record("explain_preference","スファレライト",updated_quality="sparkling")
        j.record("reject_previous","スファレライト",previous_quality="sparkling")
        self.assertEqual(validate_semantic_consistency(j).status,"CONSISTENT")
if __name__=="__main__":unittest.main()

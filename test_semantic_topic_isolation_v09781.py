import unittest
from semantic_event_journal_v09774 import SemanticEventJournal
from semantic_topic_isolation_v09781 import validate_topic_isolation

class IsolationTests(unittest.TestCase):
    def normal(self):
        j=SemanticEventJournal()
        j.record("express_preference","スファレライト")
        j.record("explain_preference","スファレライト",updated_quality="sparkling")
        j.record("switch_topic","ダイヤモンド",source_topic="スファレライト",target_topic="ダイヤモンド")
        j.record("switch_topic","スファレライト",source_topic="ダイヤモンド",target_topic="スファレライト")
        return j
    def test_roundtrip(self):
        self.assertEqual(validate_topic_isolation(self.normal()).status,"ISOLATED")
    def test_wrong_source(self):
        j=self.normal()
        j.record("switch_topic","ルビー",source_topic="サファイア",target_topic="ルビー")
        self.assertIn("broken_continuity",str(validate_topic_isolation(j).violations))
    def test_quality_on_switch(self):
        j=SemanticEventJournal()
        j.record("switch_topic","ダイヤモンド",previous_quality="sparkling",source_topic="スファレライト",target_topic="ダイヤモンド")
        self.assertIn("quality_on_switch",str(validate_topic_isolation(j).violations))
    def test_cross_topic_attribute(self):
        j=self.normal()
        j.record("explain_preference","ダイヤモンド",updated_quality="sparkling")
        self.assertIn("cross_topic_write",str(validate_topic_isolation(j).violations))
    def test_incomplete(self):
        j=SemanticEventJournal(max_events=1)
        j.record("agreement","A")
        j.record("agreement","A")
        self.assertEqual(validate_topic_isolation(j).status,"INCOMPLETE")
    def test_focus_tampering(self):
        j=self.normal()
        j.focus["ダイヤモンド"]="sparkling"
        self.assertIn("quality_focus_mismatch",str(validate_topic_isolation(j).violations))
if __name__=="__main__": unittest.main()

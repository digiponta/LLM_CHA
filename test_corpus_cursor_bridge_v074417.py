import unittest
from types import SimpleNamespace
from corpus_cursor_bridge_v074417 import bridge_records
from subject_keyed_corpus_memory_v101216 import CorpusMemoryRecord

class CorpusCursorBridgeTests(unittest.TestCase):
    def test_real_legacy_record_missing_id(self):
        row=CorpusMemoryRecord("宇宙","宇宙は膨張する","is","","宇宙は膨張する","data-nagato.txt")
        report=bridge_records([row],"宇宙")
        self.assertEqual(report.status,"MISSING_ID")
        self.assertEqual(report.missing_ids,1)
        self.assertEqual(report.evidence,())
    def test_explicit_id_ready(self):
        row=SimpleNamespace(subject="宇宙",statement="宇宙は膨張する",source="source:1",proposition_id="p001")
        report=bridge_records([row],"宇宙")
        self.assertEqual(report.status,"READY")
        self.assertEqual(report.evidence[0].proposition_id,"p001")
    def test_missing_source_rejected(self):
        row=SimpleNamespace(subject="宇宙",statement="text",source="",proposition_id="p001")
        self.assertEqual(bridge_records([row],"宇宙").status,"MISSING_SOURCE")
    def test_different_topic_excluded(self):
        row=SimpleNamespace(subject="GPU",statement="text",source="src",proposition_id="p002")
        self.assertEqual(bridge_records([row],"宇宙").count,0)
    def test_non_unverified_not_eligible(self):
        row=SimpleNamespace(subject="宇宙",statement="text",source="src",proposition_id="p003")
        self.assertEqual(bridge_records([row],"宇宙","TRUE").evidence,())

if __name__=="__main__":
    unittest.main()

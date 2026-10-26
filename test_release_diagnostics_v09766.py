import unittest
from semantic_memory_status_v09766 import parse_memory_status
from gui_runtime_version_v09766 import runtime_version

class DiagnosticsTests(unittest.TestCase):
    def test_pending(self):
        data=parse_memory_status("[Nagato Semantic Memory: corpus_records=72, subjects=56, unified_added=56, unified_preserved=0, internalized=0, pending=56]")
        self.assertEqual(data["status"],"PENDING_REINTERNALIZATION_CHECK")
        self.assertFalse(data["checkpoint_verified"])
    def test_internalized(self):
        data=parse_memory_status("[Nagato Semantic Memory: corpus_records=72, subjects=56, unified_added=0, unified_preserved=56, internalized=56, pending=0]")
        self.assertEqual(data["status"],"REPORTED_INTERNALIZED")
    def test_invalid(self):
        self.assertIsNone(parse_memory_status("not memory"))
    def test_version_nonempty(self):
        self.assertTrue(runtime_version())

if __name__=="__main__":
    unittest.main()

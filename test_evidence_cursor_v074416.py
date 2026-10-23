import unittest
from evidence_cursor_v074416 import Evidence,EvidenceCursor,render_unverified

class EvidenceCursorTests(unittest.TestCase):
    def setUp(self):
        self.a=Evidence("p1","宇宙","宇宙は膨張する。","corpus:1")
        self.b=Evidence("p2","宇宙","宇宙には銀河がある。","corpus:2")
        self.cursor=EvidenceCursor()
    def test_initially_presented_excluded(self):
        self.cursor.reset("宇宙",[self.a,self.b],"宇宙は膨張する。")
        self.assertEqual(self.cursor.next_evidence("宇宙"),self.b)
        self.assertIsNone(self.cursor.next_evidence("宇宙"))
    def test_all_presented_no_new_evidence(self):
        self.cursor.reset("宇宙",[self.a,self.b],"宇宙は膨張する。 / 宇宙には銀河がある。")
        self.assertEqual(self.cursor.remaining(),0)
    def test_no_cross_topic_leak(self):
        self.cursor.reset("宇宙",[self.a],"")
        self.assertIsNone(self.cursor.next_evidence("量子ビット"))
    def test_duplicate_next_never_repeats(self):
        self.cursor.reset("宇宙",[self.a],"")
        self.assertEqual(self.cursor.next_evidence("宇宙"),self.a)
        self.assertIsNone(self.cursor.next_evidence("宇宙"))
    def test_truth_gate(self):
        trusted=Evidence("p3","宇宙","秘密","corpus:3","TRUE")
        self.cursor.reset("宇宙",[trusted],"")
        self.assertEqual(self.cursor.remaining(),0)
    def test_provenance_required(self):
        bad=Evidence("p4","宇宙","説明","","UNVERIFIED")
        self.cursor.reset("宇宙",[bad],"")
        self.assertEqual(self.cursor.remaining(),0)
    def test_render_marks_unverified(self):
        rendered=render_unverified(self.a)
        self.assertIn("未検証",rendered)
        self.assertIn("corpus:1",rendered)
    def test_reset_discards_other_context(self):
        self.cursor.reset("宇宙",[self.a],"")
        self.cursor.reset("量子ビット",[],"")
        self.assertIsNone(self.cursor.next_evidence("宇宙"))

if __name__=="__main__":
    unittest.main()

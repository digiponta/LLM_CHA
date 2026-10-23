import ast
import unittest
from pathlib import Path
from types import SimpleNamespace
from corpus_cursor_bridge_v074417 import bridge_records
from evidence_cursor_v074416 import EvidenceCursor

class CorpusRuntimeCursorTests(unittest.TestCase):
    def test_all_shown_means_no_new_evidence(self):
        rows=[SimpleNamespace(subject="宇宙",statement="宇宙は膨張する。",source="data-nagato.txt",proposition_id="p1"),
              SimpleNamespace(subject="宇宙",statement="宇宙には銀河がある。",source="data-nagato.txt",proposition_id="p2")]
        b=bridge_records(rows,"宇宙")
        self.assertEqual(b.status,"READY")
        c=EvidenceCursor()
        c.reset("宇宙",list(b.evidence),"宇宙は膨張する。 / 宇宙には銀河がある。")
        self.assertEqual(c.remaining(),0)
        self.assertIsNone(c.next_evidence("宇宙"))
    def test_unseen_record_only_once(self):
        rows=[SimpleNamespace(subject="宇宙",statement="すでに表示済み",source="src",proposition_id="p1"),
              SimpleNamespace(subject="宇宙",statement="まだ未提示",source="src",proposition_id="p2")]
        c=EvidenceCursor()
        c.reset("宇宙",list(bridge_records(rows,"宇宙").evidence),"すでに表示済み")
        self.assertEqual(c.next_evidence("宇宙").text,"まだ未提示")
        self.assertIsNone(c.next_evidence("宇宙"))
    def test_runtime_integration_parses(self):
        source=Path(__file__).with_name("chat.py").read_text(encoding="utf-8")
        ast.parse(source)
        self.assertIn("cursor_preflight = bridge_records(",source)
        self.assertIn("corpus_evidence_cursor.next_evidence(",source)
        self.assertIn("CORPUS_EVIDENCE_CURSOR",source)
    def test_truth_gate_retained(self):
        source=Path(__file__).with_name("chat.py").read_text(encoding="utf-8")
        self.assertIn('retrieval_truth.state == "UNVERIFIED"',source)
        self.assertIn("train_ready=False, auto_promote=False",source)
if __name__=="__main__":
    unittest.main()

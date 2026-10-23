import ast
import unittest
from pathlib import Path

class WikipediaSourceScopeTests(unittest.TestCase):
    def test_continuation_preserves_origin(self):
        source=Path(__file__).with_name("wiki_evidence_continuation_v0564.py").read_text(encoding="utf-8")
        ast.parse(source)
        self.assertIn('"origin_title":title',source)
        self.assertIn('"evidence_scope":"RELATED_ARTICLE"',source)
    def test_continuation_math_gate(self):
        source=Path(__file__).with_name("wiki_evidence_continuation_v0564.py").read_text(encoding="utf-8")
        self.assertIn("safe_evidence_sentence(sentence)",source)
    def test_diagnostic_provenance(self):
        source=Path(__file__).with_name("chat.py").read_text(encoding="utf-8")
        ast.parse(source)
        self.assertIn("wiki_evidence_scope=",source)
        self.assertIn('continuation.get("origin_title","-")',source)
if __name__=="__main__":
    unittest.main()

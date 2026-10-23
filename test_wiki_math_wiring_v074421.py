import ast
import unittest
from pathlib import Path
from unittest.mock import patch
from wiki_evidence_session_v0562 import EvidenceSession

class EvidenceMathWiringTests(unittest.TestCase):
    def test_wiring(self):
        source=Path(__file__).with_name("wiki_evidence_session_v0562.py").read_text(encoding="utf-8")
        ast.parse(source)
        self.assertIn("safe_evidence_sentence(s)",source)

if __name__=="__main__":
    unittest.main()

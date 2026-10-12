import unittest
from mixed_state_gpu_accept_v02338210 import acceptance, prepare_overlay
from proposition_truth_v0233827 import proposition_id
from pathlib import Path
import tempfile

class GPUSmokeHarnessTests(unittest.TestCase):
    def test_overlay_fixture_ids(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"review.jsonl"
            prepare_overlay(p,["A","B","C","D","E"])
            content=p.read_text(encoding="utf-8")
            self.assertIn(proposition_id("宇宙","A","data-nagato.txt:subject-keyed-corpus-memory:v10.12.16"),content)
            self.assertIn('"truth_state": "FALSE"',content)
            self.assertIn('"truth_state": "TRUE"',content)

    def test_fail_closed_without_transcript(self):
        self.assertFalse(all(acceptance("",["A","B","C","D","E"]).values()))

    def test_requires_correct_id(self):
        self.assertFalse(acceptance("proposition-id=wrong, truth_state=TRUE",
                                   ["A","B","C","D","E"])["true_proposition_displayed"])

    def test_detects_reset(self):
        self.assertTrue(acceptance("参照できる話題がありません",
                                   ["A","B","C","D","E"])["reset_clears_topic"])

if __name__=="__main__":
    unittest.main()

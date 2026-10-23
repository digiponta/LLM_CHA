import tempfile
import unittest
from pathlib import Path
from dual_semantic_memory_v071 import DualMemory
from candidate_aware_fallback_v0712 import gate_review_fallback

class CandidateAwareTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        root=Path(self.tmp.name)
        self.approved=root/"approved.jsonl"
        self.pending=root/"candidates.jsonl"
        self.memory=DualMemory(self.approved,self.pending)
        self.memory.propose("v072実験の合言葉は何ですか","候補の実験回答です。","sandbox:v072")
    def tearDown(self):self.tmp.cleanup()
    def ask(self,q):
        return "候補の実験回答です。"
    def test_only_pending_candidate(self):
        result=gate_review_fallback("v072実験の合言葉は何ですか",
            self.approved,self.pending,self.ask,resolution="GATE_REVIEW",enabled=True)
        self.assertEqual(result["truth_state"],"EXPERIMENTAL_UNVERIFIED")
        self.assertFalse(result["auto_promote"])
    def test_unmatched_question_does_not_call_backend(self):
        def fail(q):raise AssertionError("backend called")
        self.assertIsNone(gate_review_fallback("宇宙",self.approved,self.pending,
            fail,resolution="GATE_REVIEW",enabled=True))
    def test_other_resolution_blocked(self):
        def fail(q):raise AssertionError("backend called")
        self.assertIsNone(gate_review_fallback("v072実験の合言葉は何ですか",
            self.approved,self.pending,fail,resolution="TRUTH_BLOCK",enabled=True))
    def test_disabled_blocked(self):
        def fail(q):raise AssertionError("backend called")
        self.assertIsNone(gate_review_fallback("v072実験の合言葉は何ですか",
            self.approved,self.pending,fail,resolution="GATE_REVIEW",enabled=False))
    def test_approved_record_not_candidate(self):
        record_id=self.memory.candidates()[0]["id"]
        self.memory.approve(record_id)
        def fail(q):raise AssertionError("backend called")
        self.assertIsNone(gate_review_fallback("v072実験の合言葉は何ですか",
            self.approved,self.pending,fail,resolution="GATE_REVIEW",enabled=True))
if __name__=="__main__":unittest.main()

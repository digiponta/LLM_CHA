import tempfile,unittest
from pathlib import Path
from dual_semantic_memory_v071 import DualMemory
from evidence_reference_v0738 import count_evidence
from approved_evidence_state_v0739 import evidence_state
from gui_status_v0732 import parse_status

class ApprovedEvidenceStateTests(unittest.TestCase):
    def test_transition(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);a=root/"a.jsonl";c=root/"c.jsonl"
            args=(a,c,"真空管","真空管は2/3乗特性。","source:v1")
            initial=evidence_state(*args,"CORPUS_MEMORY")
            self.assertEqual(initial["approval_state"],"NOT_REGISTERED")
            for _ in range(10):
                count_evidence(*args,route="CORPUS_MEMORY")
            before=evidence_state(*args,"CORPUS_MEMORY")
            self.assertEqual(before["approval_state"],"PENDING")
            self.assertEqual(before["reference_count"],10)
            count_evidence(*args,route="CORPUS_MEMORY")
            after=evidence_state(*args,"CORPUS_MEMORY")
            self.assertEqual(after["approval_state"],"APPROVED")
            self.assertEqual(after["truth_state"],"UNVERIFIED")
            self.assertEqual(len(DualMemory(a,c).approved()),1)
    def test_gui(self):
        result=parse_status("[evidence_approval: state=APPROVED, count=-, factual_truth=UNVERIFIED]")
        self.assertEqual(result["approval"],"Source approval: APPROVED")
if __name__=="__main__":unittest.main()

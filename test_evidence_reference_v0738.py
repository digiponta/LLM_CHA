import tempfile,unittest
from pathlib import Path
from dual_semantic_memory_v071 import DualMemory
from evidence_reference_v0738 import count_evidence

class EvidenceReferenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        root=Path(self.tmp.name)
        self.approved=root/"approved.jsonl"
        self.candidates=root/"candidates.jsonl"
    def tearDown(self):self.tmp.cleanup()
    def call(self,answer="記述A",route="RAW_CONCEPT_EVIDENCE"):
        return count_evidence(self.approved,self.candidates,"時間",answer,
                              "data/data-nagato.txt",route=route)
    def test_11th_reference_approves(self):
        for i in range(10):
            result=self.call()
            self.assertEqual(result["reference_count"],i+1)
            self.assertFalse(result["promoted"])
        self.assertEqual(self.call()["status"],"AUTO_APPROVED")
        mem=DualMemory(self.approved,self.candidates)
        self.assertEqual(len(mem.approved()),1)
    def test_different_answer_independent(self):
        self.call("記述A")
        self.call("記述B")
        mem=DualMemory(self.approved,self.candidates)
        self.assertEqual(sorted(r["reference_count"] for r in mem.candidates()),[1,1])
    def test_different_routes_independent(self):
        self.call(route="RAW_CONCEPT_EVIDENCE")
        self.call(route="CORPUS_MEMORY")
        self.assertEqual(len(DualMemory(self.approved,self.candidates).candidates()),2)
    def test_no_repeat_promotion(self):
        for i in range(11):self.call()
        result=self.call()
        self.assertEqual(result["status"],"ALREADY_APPROVED")
    def test_invalid(self):
        x=count_evidence(self.approved,self.candidates,"","x","src")
        self.assertEqual(x["status"],"INVALID_EVIDENCE")
if __name__=="__main__":unittest.main()

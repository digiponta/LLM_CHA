import tempfile
import unittest
from pathlib import Path
from dual_semantic_memory_v071 import DualMemory
from multi_candidate_audit_v0714 import evaluate_probes,route_probe

class MultiCandidateAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        p=Path(self.tmp.name)
        self.memory=DualMemory(p/"approved.jsonl",p/"candidate.jsonl")
        self.answers={"青い鍵は":"AO-17です。","赤い橋は":"RB-42です。","白い箱は":"WB-26です。"}
        for q,a in self.answers.items():self.memory.propose(q,a,"test-v0714")
        self.calls=[]
    def tearDown(self):self.tmp.cleanup()
    def backend(self,q):
        self.calls.append(q)
        return self.answers[q]
    def test_three_candidates(self):
        r=evaluate_probes(self.memory,self.backend,unknown_questions=["未登録の対象"])
        self.assertEqual(r["candidate_count"],3)
        self.assertEqual(r["candidate_exact"],3)
        self.assertEqual(r["unknown_rejected"],1)
        self.assertEqual(len(self.calls),3)
        self.assertFalse(r["auto_promote"])
    def test_trusted_bypass(self):
        result=route_probe("青い鍵は",self.memory,self.backend,trusted_answer="確認済み")
        self.assertEqual(result["route"],"TRUSTED")
        self.assertEqual(self.calls,[])
    def test_protected_approved_no_adapter(self):
        selected=self.memory.candidates()[0]["id"]
        self.memory.approve(selected)
        r=evaluate_probes(self.memory,self.backend,unknown_questions=["対象外"])
        self.assertTrue(r["trusted_protected_preserved"])
        self.assertEqual(r["protected_count"],1)
        self.assertEqual(len(self.calls),2)
    def test_unmatched_output_reject(self):
        r=route_probe("青い鍵は",self.memory,lambda q:"誤った内容です。")
        self.assertEqual(r["truth_state"],"UNKNOWN")
        self.assertEqual(r["route"],"EXPERIMENTAL_REJECTED")
    def test_disabled_no_call(self):
        def fail(q):raise AssertionError("adapter called")
        self.assertEqual(route_probe("青い鍵は",self.memory,fail,enabled=False)["route"],"TRUSTED_UNKNOWN")
    def test_unknown_overlap_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_probes(self.memory,self.backend,unknown_questions=["青い鍵は"])
if __name__=="__main__":unittest.main()

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from dual_semantic_memory_v071 import DualMemory
from run_multi_fact_validation_v0715 import summarize,execute,UNKNOWN_PROBES,PROTECTED_QUESTION
from multi_candidate_audit_v0714 import evaluate_probes

class MultiFactValidationTests(unittest.TestCase):
    def test_metrics_not_certified_as_factual(self):
        audit={"candidate_count":4,"candidate_exact":3,"candidate_exact_rate":.75,
               "unknown_count":2,"unknown_rejected":2,
               "protected_count":1,"trusted_protected_preserved":True}
        holdout={"holdout_count":8,"results":[{"holdout":{
            "exact_match":{"base":0.0,"experimental":.5}}}]}
        r=summarize(audit,holdout)
        self.assertEqual(r["unknown_reject_rate"],1.0)
        self.assertEqual(r["holdout_experimental_exact"],.5)
        self.assertFalse(r["approved_retention_certified"])
        self.assertFalse(r["auto_promote"])
    def test_absent_protected_probes_not_reported_as_preserved(self):
        audit={"candidate_count":0,"candidate_exact":0,"candidate_exact_rate":None,
               "unknown_count":0,"unknown_rejected":0,
               "protected_count":0,"trusted_protected_preserved":True}
        holdout={"holdout_count":8,"results":[{"holdout":{
            "exact_match":{"base":0.0,"experimental":0.0}}}]}
        r=summarize(audit,holdout)
        self.assertIsNone(r["protected_route_preserved"])
    def test_unknowns_do_not_overlap_training(self):
        from prepare_multi_knowledge_v079 import FACTS
        self.assertFalse({x[0] for x in FACTS}.intersection(UNKNOWN_PROBES))
    def test_protected_question_not_in_training(self):
        from prepare_multi_knowledge_v079 import FACTS
        self.assertNotIn(PROTECTED_QUESTION,{x[0] for x in FACTS})
    def test_read_only_route_audit_with_four_facts(self):
        with tempfile.TemporaryDirectory() as t:
            mem=DualMemory(Path(t)/"approved.jsonl",Path(t)/"candidate.jsonl")
            facts=[("青い鍵","AO-17"),("赤い橋","RB-42"),
                   ("緑の時計","GC-83"),("白い箱","WB-26")]
            for q,a in facts:mem.propose(q,a,"synthetic:test")
            mem.propose(PROTECTED_QUESTION,"承認済み回答です。","synthetic:test")
            record=next(r for r in mem.candidates() if r["question"]==PROTECTED_QUESTION)
            mem.approve(record["id"])
            calls=[]
            def backend(q):
                calls.append(q)
                return dict(facts)[q]
            result=evaluate_probes(mem,backend,unknown_questions=UNKNOWN_PROBES)
            self.assertEqual(result["candidate_exact"],4)
            self.assertEqual(result["protected_count"],1)
            self.assertTrue(result["trusted_protected_preserved"])
            self.assertEqual(result["unknown_rejected"],2)
            self.assertEqual(len(calls),4)
if __name__=="__main__":unittest.main()

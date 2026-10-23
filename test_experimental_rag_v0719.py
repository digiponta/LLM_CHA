import tempfile,unittest,json
from pathlib import Path
from dual_semantic_memory_v071 import DualMemory
from experimental_rag_v0719 import grounded_prompt,run_question
from benchmark_rag_v0719 import evaluate

class ExperimentalRAGTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        root=Path(self.tmp.name)
        self.memory=DualMemory(root/"approved.jsonl",root/"candidates.jsonl")
        self.cid=self.memory.propose("青い鍵の符号は何ですか","AO-17","synthetic:v0719")
        self.holdouts=root/"holdouts.json"
        self.holdouts.write_text(json.dumps([{"question":"青い鍵の符号を教えて",
            "reference":"AO-17","candidate_id":self.cid}],ensure_ascii=False),encoding="utf-8")
    def tearDown(self):self.tmp.cleanup()
    def test_prompt_contains_candidate_evidence(self):
        r=self.memory.candidates()[0]
        s=grounded_prompt("青い鍵の符号を教えて",r)
        self.assertIn("AO-17",s)
        self.assertIn("未承認",s)
    def test_consistent_generation_unverified(self):
        r=run_question(self.memory,"青い鍵の符号を教えて",lambda p:"AO-17")
        self.assertEqual(r["route"],"EXPERIMENTAL_RAG")
        self.assertEqual(r["truth_state"],"EXPERIMENTAL_UNVERIFIED")
        self.assertFalse(r["auto_promote"])
    def test_mismatch_rejected(self):
        r=run_question(self.memory,"青い鍵の符号を教えて",lambda p:"RB-42")
        self.assertEqual(r["route"],"EXPERIMENTAL_RAG_REJECTED")
        self.assertIsNone(r["answer"])
    def test_unknown_never_calls_generation(self):
        def forbidden(p):raise AssertionError("backend invoked")
        r=run_question(self.memory,"紫の窓の符号",forbidden)
        self.assertEqual(r["truth_state"],"UNKNOWN")
    def test_generic_subject_does_not_select_single_candidate(self):
        def forbidden(prompt):
            raise AssertionError("unrelated backend invoked")
        for question in ("紫の窓の符号", "赤い橋の符号", "符号を教えて"):
            result=run_question(self.memory,question,forbidden)
            self.assertEqual(result["truth_state"],"UNKNOWN")
    def test_optin(self):
        r=run_question(self.memory,"青い鍵の符号を教えて",
                       lambda p:1/0,enabled=False)
        self.assertEqual(r["route"],"EXPERIMENTAL_DISABLED")
    def test_comparison_metrics(self):
        def backend(prompt):
            return "AO-17"
        r=evaluate(self.memory,self.holdouts,backend)
        self.assertEqual(r["holdout_count"],1)
        self.assertEqual(r["evidence_exact"],1)
        self.assertEqual(r["adapter_exact"],1)
        self.assertEqual(r["rag_exact"],1)
        self.assertFalse(r["production_integrated"])
if __name__=="__main__":unittest.main()

import tempfile,unittest
from pathlib import Path
from evidence_dialogue_state_v02319 import DialogueState
from staged_semantic_internalization_v02325 import (
    handle,read_memory,approve,training_queue,transition,route,memorize,
)
class StagedInternalizationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.mem=str(Path(self.tmp.name)/"memory.jsonl")
    def tearDown(self):
        self.tmp.cleanup()
    def record(self):
        d,result=handle(DialogueState(),"LLMを勉強したい",self.mem)
        self.assertEqual(result["route"],"DSS_FALLBACK")
        return result["record_id"]
    def test_memorize_pending_review(self):
        key=self.record()
        r=read_memory(self.mem)[key]
        self.assertEqual((r["lifecycle"],r["teacher_status"]),("MEMORIZED","PENDING_REVIEW"))
        self.assertFalse(training_queue(self.mem))
    def test_approval_and_queue(self):
        key=self.record()
        approve(self.mem,key,"LLMの基本を順番に学びましょう。")
        self.assertEqual(len(training_queue(self.mem)),1)
    def test_duplicate_preserves_approval(self):
        key=self.record()
        approve(self.mem,key,"LLMの基本を順番に学びましょう。")
        handle(DialogueState(),"LLMを勉強したい",self.mem)
        self.assertEqual(read_memory(self.mem)[key]["teacher_status"],"APPROVED")
        self.assertEqual(len(read_memory(self.mem)),1)
    def test_reject_invalid_transition(self):
        key=self.record()
        with self.assertRaises(ValueError):transition(self.mem,key,"TRAINING")
        with self.assertRaises(ValueError):transition(self.mem,key,"INTERNALIZED")
    def test_candidate_and_evidence_guard(self):
        key=self.record()
        approve(self.mem,key,"まずLLMの構造を確認しましょう。")
        transition(self.mem,key,"TRAINING")
        with self.assertRaises(ValueError):transition(self.mem,key,"VALIDATING")
        transition(self.mem,key,"VALIDATING",checkpoint="model/candidate.pt")
        with self.assertRaises(ValueError):transition(self.mem,key,"INTERNALIZED",evidence={"free_generation":True})
        evidence={k:True for k in ("free_generation","unseen_generalization","retention","purpose_fidelity")}
        transition(self.mem,key,"INTERNALIZED",evidence=evidence)
        self.assertEqual(route(self.mem,key),"LLM_DIRECT_ELIGIBLE")
        transition(self.mem,key,"FAILED",evidence={"reason":"runtime regression"})
        self.assertEqual(route(self.mem,key),"DSS_FALLBACK")
    def test_confirmation_not_teacher(self):
        _,r=handle(DialogueState(),"Pythonに興味がある",self.mem)
        self.assertIsNone(r["record_id"])
        self.assertEqual(read_memory(self.mem),{})
if __name__=="__main__":unittest.main()

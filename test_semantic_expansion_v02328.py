import unittest,tempfile
from pathlib import Path
from evidence_dialogue_state_v02319 import DialogueState
from staged_semantic_internalization_v02325 import handle,approve,read_memory
from semantic_memory_expansion_v02328 import expand,export,load_rows,approve_variant,approved_training
from train_semantic_expansion_v02328 import get_sets
class ExpansionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.mem=str(Path(self.tmp.name)/"memory.jsonl")
        self.exp=str(Path(self.tmp.name)/"expansion.jsonl")
        _,r=handle(DialogueState(),"LLMを勉強したい",self.mem)
        self.key=r["record_id"]
    def tearDown(self):self.tmp.cleanup()
    def test_unapproved_rejected(self):
        with self.assertRaises(ValueError):expand(read_memory(self.mem)[self.key])
    def test_expansion_requires_review(self):
        approve(self.mem,self.key,"まずLLMの仕組みを学びましょう。")
        counts=export(self.mem,self.exp)
        self.assertEqual(counts,{"APPROVED":1,"PENDING_REVIEW":2})
        self.assertEqual(len(approved_training(self.exp)),1)
        with self.assertRaisesRegex(ValueError,"No reviewed expansions"):
            get_sets(self.exp)
    def test_reviewed_expansion_training(self):
        approve(self.mem,self.key,"まずLLMの仕組みを学びましょう。")
        export(self.mem,self.exp)
        r=load_rows(self.exp)
        variant=next(x for x in r if x["variant_type"]=="paraphrase")
        approve_variant(self.exp,variant["id"])
        orig,expanded=get_sets(self.exp)
        self.assertEqual((len(orig),len(expanded)),(1,2))
        self.assertTrue(all(x["answer"]=="まずLLMの仕組みを学びましょう。" for x in expanded))
        with self.assertRaises(KeyError):approve_variant(self.exp,"not_found")
    def test_eval_probe_separation(self):
        from evaluate_semantic_transfer_v02327 import PROBES
        approve(self.mem,self.key,"まずLLMの仕組みを学びましょう。")
        export(self.mem,self.exp)
        corpus="\n".join(r["prompt"] for r in load_rows(self.exp))
        for probe in PROBES:self.assertNotIn(probe["user"],corpus)
if __name__=="__main__":unittest.main()

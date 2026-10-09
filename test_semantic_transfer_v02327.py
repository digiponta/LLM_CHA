import tempfile,unittest
from pathlib import Path
from unittest.mock import Mock
from evidence_dialogue_state_v02319 import DialogueState
from staged_semantic_internalization_v02325 import handle,approve,transition
from evaluate_semantic_transfer_v02327 import probes_for,prompt_for,evaluate,PROBES,LEGACY

class SemanticTransferTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=str(Path(self.tmp.name)/"mem.jsonl")
        _,r=handle(DialogueState(),"LLMを勉強したい",self.path)
        self.key=r["record_id"]
        approve(self.path,self.key,"LLMの基本構造を学びましょう。")
        transition(self.path,self.key,"TRAINING")
        transition(self.path,self.key,"VALIDATING",checkpoint="candidate.pt")
    def tearDown(self):self.tmp.cleanup()
    def test_unseen_probes_have_no_teacher_text(self):
        ckpt,rows=probes_for(self.path)
        self.assertEqual(ckpt,"candidate.pt")
        self.assertEqual(len(rows),1+len(PROBES)+len(LEGACY))
        self.assertEqual(len({prompt_for(x) for x in rows}),len(rows))
        self.assertFalse(any(x["user"]=="LLMを勉強したい" for x in PROBES))
    def test_prompt_matches_sft(self):
        _,rows=probes_for(self.path)
        self.assertEqual(prompt_for(rows[0]),"話題: LLM\n目的: 学習\n人: LLMを勉強したい\nAI: ")
    def test_mock_generator_same_conditions(self):
        _,rows=probes_for(self.path)
        base=Mock();candidate=Mock()
        base.generate.return_value={"text":"before","generated_tokens":3,"elapsed_seconds":0.1}
        candidate.generate.return_value={"text":"after","generated_tokens":3,"elapsed_seconds":0.2}
        out=evaluate(base,candidate,rows[:2],max_new_tokens=12)
        self.assertEqual(len(out),2)
        self.assertTrue(all(v["manual_review"]["candidate"]["fluency"] is None for v in out))
        for model in (base,candidate):
            self.assertEqual(model.generate.call_count,2)
            self.assertTrue(all(c.kwargs["temperature"]==0 and c.kwargs["max_new_tokens"]==12 for c in model.generate.call_args_list))
    def test_no_validating_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):probes_for(str(Path(tmp)/"not-found.jsonl"))
if __name__=="__main__":unittest.main()

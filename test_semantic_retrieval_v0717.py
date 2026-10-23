import tempfile,unittest,json
from pathlib import Path
from dual_semantic_memory_v071 import DualMemory
from prepare_multi_knowledge_v079 import FACTS
from experimental_semantic_retrieval_v0717 import route,retrieve
from evaluate_semantic_retrieval_v0717 import evaluate,UNKNOWN

class CandidateRetrievalTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        root=Path(self.tmp.name)
        self.approved=root/"approved.jsonl"
        self.candidates=root/"candidates.jsonl"
        self.holdouts=root/"holdouts.json"
        self.memory=DualMemory(self.approved,self.candidates)
        rows=[]
        for q,a,variants in FACTS:
            id=self.memory.propose(q,a,"synthetic:test")
            rows.extend({"question":v,"reference":a,"candidate_id":id} for v in variants)
        self.holdouts.write_text(json.dumps(rows,ensure_ascii=False),encoding="utf-8")
    def tearDown(self):self.tmp.cleanup()
    def test_candidate_exact(self):
        for q,answer,_ in FACTS:
            self.assertEqual(route(self.memory,q)["answer"],"【未承認・候補知識】"+answer)
    def test_paraphrase_holdouts(self):
        report=evaluate(self.approved,self.candidates,self.holdouts)
        self.assertEqual(report["holdout_count"],8)
        self.assertEqual(report["retrieval_correct"],8)
        self.assertEqual(report["unknown_rejected"],2)
    def test_unknowns_blocked(self):
        for q in UNKNOWN:
            self.assertEqual(route(self.memory,q)["truth_state"],"UNKNOWN")
    def test_ambiguous_rejected(self):
        self.memory.propose("v079実験で青い鍵の番号は何ですか","DIFFERENT","synthetic:test")
        self.assertEqual(retrieve(self.memory,"青い鍵")["status"],"UNKNOWN")
    def test_no_promote(self):
        self.assertFalse(route(self.memory,FACTS[0][0])["auto_promote"])
if __name__=="__main__":unittest.main()

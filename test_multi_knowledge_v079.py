import tempfile
import unittest
from pathlib import Path
from prepare_multi_knowledge_v079 import FACTS,prepare
from dual_semantic_memory_v071 import DualMemory
from benchmark_generalization_v078 import validate_holdouts
import json

class MultiKnowledgeTests(unittest.TestCase):
    def test_four_distinct_facts(self):
        self.assertEqual(len(FACTS),4)
        self.assertEqual(len({q for q,_,_ in FACTS}),4)
        self.assertEqual(len({a for _,a,_ in FACTS}),4)
    def test_fixture_isolated(self):
        with tempfile.TemporaryDirectory() as root:
            result=prepare(Path(root)/"fixture")
            m=DualMemory(result["approved"],result["candidates"])
            self.assertEqual(len(m.candidates()),4)
            self.assertEqual(m.approved(),[])
            self.assertTrue(all(r["status"]=="PENDING" for r in m.candidates()))
    def test_holdouts_not_exact_training_questions(self):
        with tempfile.TemporaryDirectory() as root:
            result=prepare(Path(root)/"fixture")
            m=DualMemory(result["approved"],result["candidates"])
            holdouts=json.loads(Path(result["holdouts"]).read_text(encoding="utf-8"))
            self.assertEqual(len(holdouts),8)
            validate_holdouts(holdouts,[r["question"] for r in m.candidates()])
    def test_reject_existing_fixture(self):
        with tempfile.TemporaryDirectory() as root:
            prepare(Path(root)/"fixture")
            with self.assertRaises(FileExistsError):prepare(Path(root)/"fixture")
if __name__=="__main__":unittest.main()

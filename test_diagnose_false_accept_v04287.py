"""Structural tests for read-only v0.4.28.7 diagnostics."""
import unittest
from diagnose_false_accept_v04287 import analyze
class Tests(unittest.TestCase):
    def fixture(self):
        records=[{"id":f"{cat}{i:02d}","turn":1,"question":"質問","answer":"回答","gate_resolution":"ACCEPT","abstention":False,"flags":[]} for cat,n in (("A",12),("B",12),("C",8),("D",8),("E",8),("G",4)) for i in range(1,n+1)]
        records += [{"id":f"F{i}","turn":t,"question":"質問","answer":"回答","gate_resolution":"ACCEPT","abstention":False,"flags":[]} for i in range(1,5) for t in range(1,4)]
        return {"records":records}
    def test_all_records(self):
        r=analyze(self.fixture())
        self.assertEqual(r["total_turns"],64)
        self.assertEqual(r["accept_relevance_review_count"],64)
        self.assertFalse(r["human_quality_evaluated"])
    def test_mixed_paraphrase(self):
        d=self.fixture()
        next(r for r in d["records"] if r["id"]=="B01")["abstention"]=True
        result=analyze(d)
        self.assertTrue(next(x for x in result["paraphrase_sets"] if x["set"]=="gpu_definition")["mixed_abstention"])
    def test_missing_comparison(self):
        d=self.fixture();d["records"]=[r for r in d["records"] if r["id"]!="C02"]
        with self.assertRaises(ValueError):analyze(d)
    def test_duplicate_record(self):
        d=self.fixture();d["records"][1]["id"]=d["records"][0]["id"]
        with self.assertRaises(ValueError):analyze(d)
    def test_not_auto_failure(self):
        r=analyze(self.fixture())["records"][0]
        self.assertIsNone(r["manual_labels"]["answer_relevant"])
        self.assertNotIn("FALSE_ACCEPT",r["flags"])
if __name__=="__main__":unittest.main()

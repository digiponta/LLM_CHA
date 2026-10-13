"""Synthetic regression tests for read-only v0.4.28.6 triage."""
import unittest
from eval_quality_v04286 import gate_resolution, triage

class QualityTriageTests(unittest.TestCase):
    def sample(self):
        return {"groups": [
            {"id":"A06","mode":"SINGLE","status":"FINISHED","turns":[
                {"question":"少し話さない？","response":"未学習です",
                 "gate":"[gate=UNKNOWN, resolution=GATE_REVIEW]"}]},
            {"id":"G01","mode":"SINGLE","status":"FINISHED","turns":[
                {"question":"GPUについて一文で説明して。","response":"GPUは並列処理が得意。",
                 "gate":"[gate=KNOWN, resolution=ACCEPT]"}]},
            {"id":"F1","mode":"MULTI","status":"FINISHED","turns":[
                {"question":"読書が好き？","response":"好き。","gate":None},
                {"question":"なぜ？","response":None,"gate":None},
                {"question":"続けて","response":"文�字","gate":None}]}
        ]}
    def test_abstention_vs_capture(self):
        r=triage(self.sample())
        self.assertEqual(r["captured_answers"],4)
        self.assertEqual(r["abstentions"],1)
        self.assertEqual(r["total_turns"],5)
        self.assertEqual(r["replacement_in_answers"],1)
        self.assertFalse(r["human_quality_evaluated"])
    def test_resolution(self):
        self.assertEqual(gate_resolution("[gate=KNOWN, resolution=ACCEPT]"),"ACCEPT")
        self.assertEqual(gate_resolution(None),"NOT_RECORDED")
    def test_manual_unscored(self):
        for record in triage(self.sample())["records"]:
            self.assertIsNone(record["human_annotation"]["relevance"])
    def test_duplicates_rejected(self):
        doc=self.sample()
        doc["groups"][1]["id"]="A06"
        with self.assertRaises(ValueError):triage(doc)
    def test_missing_not_abstention(self):
        record=next(r for r in triage(self.sample())["records"] if r["answer"] is None)
        self.assertFalse(record["abstention"])
        self.assertIn("MISSING_CAPTURE",record["flags"])
if __name__=="__main__":unittest.main()

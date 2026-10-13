import json
import unittest
from evaluate_proposition_holdout_v0413 import FIXTURE,evaluate,evidence,score
from article_proposition_alignment_v0412 import align

class HoldoutTests(unittest.TestCase):
    def test_fixture_count(self):
        self.assertEqual(evaluate()["case_count"],30)
    def test_fixture_multiple_concepts(self):
        rows=json.loads(FIXTURE.read_text(encoding="utf-8"))["cases"]
        self.assertGreaterEqual(len({x["concept"] for x in rows}),8)
    def test_totals_baseline(self):
        d=evaluate()["baseline_v0410"]
        self.assertEqual(d["tp"]+d["fp"]+d["tn"]+d["fn"],30)
    def test_totals_expanded(self):
        d=evaluate()["expanded_v0412"]
        self.assertEqual(d["tp"]+d["fp"]+d["tn"]+d["fn"],30)
    def test_deterministic(self):
        self.assertEqual(evaluate(),evaluate())
    def test_frozen_fixture_digest(self):
        self.assertEqual(len(evaluate()["fixture_sha256"]),64)
    def test_separate_labels(self):
        rows=json.loads(FIXTURE.read_text(encoding="utf-8"))["cases"]
        self.assertGreater(sum(x["expected_extract"] for x in rows),0)
        self.assertGreater(sum(not x["expected_extract"] for x in rows),0)
    def test_guard_safety(self):
        d=evaluate()
        self.assertEqual(d["truth_promotions"],0)
        self.assertEqual(d["semantic_memory_writes"],0)
        self.assertFalse(d["training_enabled"])
    def test_source_span(self):
        row={"id":"x","concept":"GPU","text":"GPUとは並列計算装置である。"}
        d=align(evidence(row))
        self.assertEqual(d["propositions"][0]["evidence_text"],row["text"])
    def test_score_repeatable(self):
        rows=json.loads(FIXTURE.read_text(encoding="utf-8"))["cases"]
        self.assertEqual(score(rows,align),score(rows,align))
if __name__=="__main__":unittest.main()

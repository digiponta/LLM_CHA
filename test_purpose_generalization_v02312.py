import unittest
from prepare_purpose_generalization_v02312 import fixture,SEQUENCES
from evaluate_purpose_generalization_v02312 import (
    evaluate_single,evaluate_sequences,reliability)
class GeneralizationTests(unittest.TestCase):
    def test_count_and_ids(self):
        rows=fixture()
        self.assertEqual(len(rows),24)
        self.assertEqual(len({r["id"] for r in rows}),24)
    def test_categories(self):
        kinds={x["id"].split("-")[0] for x in fixture()}
        self.assertEqual(kinds,{"learn","dev","error","chat","amb","neg"})
    def test_evaluation_total(self):
        rows=evaluate_single(fixture())
        self.assertEqual(len(rows),24)
        self.assertTrue(all(isinstance(r["correct"],bool) for r in rows))
    def test_reliability_counts(self):
        rows=evaluate_single(fixture())
        bins=reliability(rows)
        self.assertEqual(sum(r["count"] for r in bins),20)
    def test_sequence_count(self):
        result=evaluate_sequences(SEQUENCES)
        self.assertEqual(len(result),5)
    def test_yes_no_baseline(self):
        result={r["id"]:r for r in evaluate_sequences(SEQUENCES)}
        self.assertTrue(result["confirm-yes"]["correct"])
        self.assertTrue(result["confirm-no-correct"]["correct"])
    def test_unknown_clarification(self):
        result={r["id"]:r for r in evaluate_sequences(SEQUENCES)}
        self.assertTrue(result["unknown-clarify"]["correct"])
if __name__=="__main__":unittest.main()

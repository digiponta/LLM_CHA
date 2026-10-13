import unittest
from persona_quality_dimensions_v0426 import evaluate_dimensions, AXES

def binary(i,bad=False):
    return dict(id=i,split="development",question="質問"+i,answer="回答",
                gold_inappropriate=bad,agreement=.5,semantic_agreement=.9,
                runtime_accepted=True,label_source="HUMAN_REVIEW")
def dimensions(i,**overrides):
    return dict(id=i,reviewer="human",relevance=overrides.get("relevance","PASS"),
                fluency=overrides.get("fluency","PASS"),
                persona_consistency=overrides.get("persona_consistency","UNCERTAIN"),
                grounding=overrides.get("grounding","NOT_APPLICABLE"))
class DimensionTests(unittest.TestCase):
    def test_pending_without_annotations(self):
        r=evaluate_dimensions([binary("a")],[])
        self.assertEqual(r["pending_ids"],["a"])
        self.assertEqual(r["reviewed_count"],0)
    def test_review_and_axis_counts(self):
        r=evaluate_dimensions([binary("a",True),binary("b")],
                              [dimensions("a",relevance="FAIL"),dimensions("b")])
        self.assertEqual(r["axis_counts"]["relevance"]["FAIL"],1)
        self.assertEqual(r["binary_dimension_disagreements"]["inappropriate"],1)
        self.assertEqual(r["pending_ids"],[])
    def test_no_auto_inference(self):
        r=evaluate_dimensions([binary("a",True)],[dimensions("a")])
        self.assertEqual(r["binary_dimension_disagreements"]["inappropriate_with_no_axis_fail"],1)
        self.assertFalse(r["independent_holdout_claimed"])
    def test_invalid_label(self):
        with self.assertRaises(ValueError):
            evaluate_dimensions([binary("a")],[dimensions("a",fluency="GOOD")])
    def test_core_not_applicable(self):
        with self.assertRaises(ValueError):
            evaluate_dimensions([binary("a")],[dimensions("a",relevance="NOT_APPLICABLE")])
    def test_duplicate_review(self):
        with self.assertRaises(ValueError):
            evaluate_dimensions([binary("a")],[dimensions("a"),dimensions("a")])
    def test_unrecognized_id(self):
        with self.assertRaises(ValueError):
            evaluate_dimensions([binary("a")],[dimensions("b")])
    def test_no_runtime_mutation(self):
        row=binary("a")
        original=dict(row)
        evaluate_dimensions([row],[dimensions("a",relevance="FAIL")])
        self.assertEqual(row,original)
if __name__=="__main__":unittest.main()

import unittest
from benchmark_generalization_v078 import make_holdout,validate_holdouts,DEFAULT_VARIANTS

class GeneralizationTests(unittest.TestCase):
    def setUp(self):
        self.candidate={"id":"example","question":"v072実験の合言葉は何ですか",
                        "answer":"候補の実験回答です。","source_id":"sandbox-manual:v072"}
    def test_default_holdout_five(self):
        rows=make_holdout(self.candidate)
        self.assertEqual(len(rows),5)
        self.assertEqual(len({r["question"] for r in rows}),5)
        self.assertTrue(all(r["reference"]==self.candidate["answer"] for r in rows))
    def test_train_overlap_rejected(self):
        rows=[{"question":self.candidate["question"],"reference":"x"}]
        with self.assertRaises(ValueError):
            validate_holdouts(rows,[self.candidate["question"]])
    def test_duplicate_holdout_rejected(self):
        rows=[{"question":"言い換え","reference":"x"}]*2
        with self.assertRaises(ValueError):
            validate_holdouts(rows,[self.candidate["question"]])
    def test_empty_rejected(self):
        with self.assertRaises(ValueError):
            validate_holdouts([],[])
    def test_invalid_holdout_rejected(self):
        with self.assertRaises(ValueError):
            validate_holdouts([{"question":"test"}],[])
    def test_wrong_training_example_refused(self):
        with self.assertRaises(ValueError):
            make_holdout(dict(self.candidate,question="別の問い"))
    def test_no_exact_training_question(self):
        rows=make_holdout(self.candidate)
        self.assertIs(validate_holdouts(rows,[self.candidate["question"]]),rows)
if __name__=="__main__": unittest.main()

import unittest
from pathlib import Path
from train_b_raw_epoch_sweep_v01329 import plan,EPOCHS
from evaluate_b_raw_epoch_curve_v01329 import summarize

class EpochSweepTests(unittest.TestCase):
    def test_epochs(self):
        self.assertEqual(EPOCHS,(1,2,4,8))
    def test_independent_models(self):
        jobs=plan(Path("results/experiment"))
        self.assertEqual(len({x["checkpoint"] for x in jobs}),4)
        self.assertEqual(len({x["state"] for x in jobs}),4)
    def test_metrics(self):
        metrics=summarize([{"first_rank":1,"first_nll":1.0,"answer_nll":2.0},
                           {"first_rank":3,"first_nll":3.0,"answer_nll":4.0}])
        self.assertEqual(metrics["first_rank1"],1)
        self.assertEqual(metrics["mean_first_nll"],2.0)

if __name__=="__main__":unittest.main()

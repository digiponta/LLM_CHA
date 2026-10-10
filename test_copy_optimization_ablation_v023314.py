import unittest
from copy_optimization_ablation_v023314 import ARMS,plan
from input_output_copy_learning_v02339 import TRAIN_TEXTS
class AblationTests(unittest.TestCase):
    def test_four_factorial_arms(self):
        self.assertEqual(len(ARMS),4)
        self.assertEqual({(lr,replay) for _,lr,replay in ARMS},
                         {(5e-6,True),(5e-6,False),(2e-4,True),(2e-4,False)})
    def test_deterministic_plan(self):
        self.assertEqual(plan(3,42),plan(3,42))
        self.assertNotEqual(plan(3,42),plan(3,43))
    def test_each_epoch_visits_all_train_items(self):
        for epoch in plan(4,42):
            self.assertEqual(len(epoch),len(TRAIN_TEXTS))
            self.assertEqual(set(i for i,_ in epoch),set(range(len(TRAIN_TEXTS))))
    def test_plan_replay_indices_nonnegative(self):
        for epoch in plan(2,42):
            self.assertTrue(all(i>=0 for _,i in epoch))
if __name__=="__main__":unittest.main()

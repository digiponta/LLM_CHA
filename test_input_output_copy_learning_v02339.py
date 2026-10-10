import unittest
from unittest.mock import patch
import input_output_copy_learning_v02339 as m
class CopyLearningTests(unittest.TestCase):
    def test_splits(self):
        self.assertTrue(m.validate_splits())
        self.assertEqual(len(m.TRAIN_TEXTS),20)
        self.assertEqual(len(m.VAL_TEXTS),5)
        self.assertEqual(len(m.TESTS),8)
    def test_prompt_answer(self):
        for row in m.rows(m.TRAIN_TEXTS):
            self.assertTrue(row["prompt"].startswith("人: "))
            self.assertTrue(row["prompt"].endswith("\nAI: "))
            self.assertIn(row["answer"],row["prompt"])
    def test_seen_and_unseen_are_disjoint(self):
        train=set(m.TRAIN_TEXTS)
        self.assertTrue(all(text not in train for _,text in m.TESTS))
    def test_leakage_rejected(self):
        with patch.object(m,"VAL_TEXTS",m.VAL_TEXTS+[m.TRAIN_TEXTS[0]]):
            with self.assertRaisesRegex(ValueError,"leakage"):m.validate_splits()
    def test_duplicate_rejected(self):
        with patch.object(m,"TRAIN_TEXTS",m.TRAIN_TEXTS+[m.TRAIN_TEXTS[0]]):
            with self.assertRaisesRegex(ValueError,"Duplicate"):m.validate_splits()
if __name__=="__main__":unittest.main()

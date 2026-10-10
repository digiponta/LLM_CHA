import unittest
from language_foundation_recovery_v02335 import TRAIN,VALID,HOLDOUT,rowset,validate_splits

class LanguageFoundationTests(unittest.TestCase):
    def test_disjoint_prompts(self):
        self.assertTrue(validate_splits())
    def test_rows_have_answers(self):
        for split in (TRAIN,VALID):
            self.assertTrue(split)
            self.assertTrue(all(p.startswith("人: ") and "\nAI: " in p and a for p,a in split))
    def test_unique_examples(self):
        rows=rowset(TRAIN+VALID)
        self.assertEqual(len(rows),len({r["id"] for r in rows}))
    def test_evaluation_not_trained(self):
        train_prompts={p for p,_ in TRAIN+VALID}
        self.assertTrue(all(p not in train_prompts for _,p in HOLDOUT))
    def test_validation_detects_leakage(self):
        from unittest.mock import patch
        with patch("language_foundation_recovery_v02335.HOLDOUT",[("leak",TRAIN[0][0])]):
            with self.assertRaisesRegex(ValueError,"overlap"):
                validate_splits()
if __name__=="__main__":unittest.main()

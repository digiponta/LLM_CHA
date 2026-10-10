import unittest
from unittest.mock import patch
from language_foundation_generalization_v02336 import (
    TRAIN_FACTS,VALID_FACTS,HOLDOUT_TOPICS,HOLDOUT,splits,validate)
class GeneralizationTests(unittest.TestCase):
    def test_splits(self):
        self.assertTrue(validate())
        train,val=splits()
        self.assertEqual(len(train),len(TRAIN_FACTS)*3+10)
        self.assertEqual(len(val),len(VALID_FACTS)*3+2)
    def test_no_topic_overlap(self):
        self.assertFalse(set(TRAIN_FACTS)&set(VALID_FACTS))
        self.assertFalse(set(HOLDOUT_TOPICS)&(set(TRAIN_FACTS)|set(VALID_FACTS)))
    def test_duplicate_training_prompt_rejected(self):
        import language_foundation_generalization_v02336 as module
        with patch.object(module,"TRAIN_FACTS",dict(list(TRAIN_FACTS.items())+[("CPU",TRAIN_FACTS["CPU"])])):
            self.assertTrue(module.validate())
        with patch.object(module,"HOLDOUT",HOLDOUT+[HOLDOUT[0]]):
            with self.assertRaisesRegex(ValueError,"Duplicated"):module.validate()
    def test_topic_leakage_detected(self):
        import language_foundation_generalization_v02336 as module
        with patch.object(module,"VALID_FACTS",{**VALID_FACTS,"CPU":TRAIN_FACTS["CPU"]}):
            with self.assertRaisesRegex(ValueError,"Topic leakage"):module.validate()
    def test_output_shapes(self):
        train,val=splits()
        self.assertTrue(all(r["prompt"].startswith("人: ") and "\nAI: " in r["prompt"] and r["answer"] for r in train+val))
if __name__=="__main__":unittest.main()

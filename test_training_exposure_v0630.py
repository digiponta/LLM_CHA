import unittest
from pathlib import Path
from online_train import ConversationDataset, pair_fingerprint, split_incremental_pairs

class TrainingExposureTests(unittest.TestCase):
    def test_pair_fingerprint(self):
        self.assertEqual(pair_fingerprint("猫", "動物"),pair_fingerprint(" 猫 ", "動物 "))
    def test_pending_pair_in_train(self):
        pair=("クルマ", "車両")
        train,val=split_incremental_pairs([pair]*4,[("a","b"),("c","d")],
                                            {pair_fingerprint(*pair)},validation_ratio=.5)
        self.assertEqual(train.count(pair),4)
        self.assertNotIn(pair,val)
    def test_optimizer_exposure_commit_guard_present(self):
        source=Path(__file__).with_name("online_train.py").read_text(encoding="utf-8")
        self.assertIn('training_exposure[fp] = training_exposure.get(fp, 0) + 1',source)
        self.assertIn('if training_exposure.get(pair_fingerprint(u, a), 0) > 0',source)
        self.assertIn('"training_exposure_counts_v0630"',source)
if __name__=="__main__":unittest.main()

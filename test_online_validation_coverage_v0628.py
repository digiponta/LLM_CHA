import unittest
from unittest.mock import patch
from online_train import split_incremental_pairs, pair_fingerprint

class OnlineValidationCoverageTests(unittest.TestCase):
    def test_pending_pair_always_trained_with_one_copy(self):
        pending=("新規質問","新規回答")
        history=[("旧質問"+str(i),"旧回答"+str(i)) for i in range(15)]
        with patch("random.shuffle",side_effect=lambda seq: seq.reverse()):
            train,val=split_incremental_pairs([pending],history,
                    {pair_fingerprint(*pending)},validation_ratio=0.9)
        self.assertIn(pending,train)
        self.assertNotIn(pending,val)

    def test_pending_pair_weighted_copies_cannot_be_validation_only(self):
        pending=("猫とは","猫の説明")
        replay=[("既知"+str(i),"回答"+str(i)) for i in range(12)]
        train,val=split_incremental_pairs([pending]*4,replay,
                    {pair_fingerprint(*pending)},validation_ratio=0.95)
        self.assertEqual(train.count(pending),4)
        self.assertEqual(val.count(pending),0)

    def test_no_pair_leakage(self):
        pending=("自動車","車両")
        other=[("Q"+str(i),"A"+str(i)) for i in range(12)]
        train,val=split_incremental_pairs([pending],other+other,
                    {pair_fingerprint(*pending)},validation_ratio=0.3)
        self.assertTrue(val)
        self.assertFalse({pair_fingerprint(*x) for x in train} &
                         {pair_fingerprint(*x) for x in val})

    def test_only_pending_and_no_replay(self):
        pending=("唯一","学習対象")
        train,val=split_incremental_pairs([pending]*4,[],
                    {pair_fingerprint(*pending)},validation_ratio=0.9)
        self.assertEqual(len(train),4)
        self.assertEqual(val,[])

    def test_fail_closed_on_missing_pending(self):
        with self.assertRaises(ValueError):
            split_incremental_pairs([], [("別","別")],
                    {pair_fingerprint("未収録","回答")})

if __name__=="__main__":
    unittest.main()

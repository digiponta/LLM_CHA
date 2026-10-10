import unittest
import torch
from algorithmic_copy_generalization_v023320 import make_pools,make_examples,encode_pair,generation

class AlgorithmicCopyTests(unittest.TestCase):
    def test_disjoint_token_pools(self):
        known,held=make_pools(8000)
        self.assertFalse(set(known)&set(held))
        self.assertNotIn(7,known+held)
    def test_split_uniqueness_and_reproducibility(self):
        known,held=make_pools(8000)
        a=make_examples(42,known,held,15,8,8)
        self.assertEqual(a,make_examples(42,known,held,15,8,8))
        all_seq=[tuple(s) for group in a.values() for s in group]
        self.assertEqual(len(all_seq),len(set(all_seq)))
    def test_heldout_token_ids(self):
        known,held=make_pools(8000)
        a=make_examples(42,known,held,10,5,5)
        self.assertTrue(all(set(s)<=set(known) for s in a["train"]))
        self.assertTrue(all(set(s)<=set(held) for s in a["unseen_token_ids"]))
    def test_label_alignment(self):
        x,y=encode_pair([10,11],7,2,3,32)
        self.assertEqual(x.tolist(),[2,7,10,11,7,10,11])
        self.assertEqual(y.tolist(),[-100,-100,-100,-100,10,11,3])
    def test_context_limit(self):
        with self.assertRaises(ValueError):encode_pair([10,11],7,2,3,5)
if __name__=="__main__":unittest.main()

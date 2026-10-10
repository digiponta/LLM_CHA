import unittest
from token_copy_factorial_v023322 import ARMS,pools,data_sequences,prepare

class FactorialCopyTests(unittest.TestCase):
    def test_factorial_design(self):
        self.assertEqual(set((length,n) for _,length,n in ARMS),
                         {(8,64),(18,64),(8,80),(18,80)})
    def test_token_pools_are_disjoint(self):
        known,added,novel=pools(8000)
        self.assertEqual([len(known),len(added),len(novel)],[64,16,16])
        self.assertFalse(set(known)&set(added))
        self.assertFalse(set(known+added)&set(novel))
    def test_examples_respect_ranges_and_exclusions(self):
        excluded=[[8,9],[9,8]]
        samples=data_sequences(1,[8,9,10],30,2,5,excluded)
        self.assertFalse(set(map(tuple,samples))&set(map(tuple,excluded)))
        self.assertEqual(len(samples),len(set(map(tuple,samples))))
        self.assertTrue(all(2<=len(x)<=5 for x in samples))
    def test_eval_deterministic_and_no_overlap(self):
        a=prepare(42,20,10,10)
        self.assertEqual(a,prepare(42,20,10,10))
        all_rows=[tuple(x) for group in a.values() for x in group]
        self.assertEqual(len(all_rows),len(set(all_rows)))
        self.assertTrue(all(12<=len(x)<=18 for x in a["long"]))
        self.assertTrue(all(set(x)<=set(range(88,104)) for x in a["novel_only"]))
    def test_invalid_requests(self):
        with self.assertRaises(ValueError):data_sequences(1,[8,9],0,2,8)
        with self.assertRaises(ValueError):pools(50)
if __name__=="__main__":unittest.main()

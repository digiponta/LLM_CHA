import unittest
from evaluate_independent_ood_transfer_v023319 import FRESH,build_groups,compare_models
from evaluate_copy_ood_robustness_v023317 import validate_groups

class IndependentTransferTests(unittest.TestCase):
    def test_fresh_group_structure(self):
        self.assertEqual(set(FRESH),{"new_lexicon","new_syntax","long_context",
                                   "multi_sentence","numeric_ascii","unicode_fidelity"})
        self.assertTrue(validate_groups(FRESH))
    def test_fresh_not_old_diagnostics(self):
        fresh,old=build_groups()
        newer={v for key,values in fresh.items() if key!="in_grammar_control" for v in values}
        prior={v for values in old.values() for v in values}
        self.assertFalse(newer&prior)
    def test_control_is_separate(self):
        fresh,_=build_groups()
        self.assertEqual(len(fresh["in_grammar_control"]),20)
        self.assertTrue(validate_groups(fresh))
    def test_duplicate_rejected(self):
        with self.assertRaises(ValueError):
            validate_groups({"group1":["same"],"group2":["same"]})
if __name__=="__main__":unittest.main()

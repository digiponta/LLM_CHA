import unittest
from truth_aware_corpus_gate_v023373 import corpus_answer_decision

class CorpusTruthGateTests(unittest.TestCase):
    def test_verified_true_allows(self):
        self.assertEqual(corpus_answer_decision("TRUE",True),"ALLOW_VERIFIED_STATE")
    def test_unverified_blocks(self):
        self.assertEqual(corpus_answer_decision("UNVERIFIED",True),"BLOCK_UNVERIFIED_CORPUS")
    def test_contested_blocks(self):
        self.assertEqual(corpus_answer_decision("CONTESTED",True),"BLOCK_UNVERIFIED_CORPUS")
    def test_false_defers(self):
        self.assertEqual(corpus_answer_decision("FALSE",True),"DEFER_TRUTH_CORRECTION")
    def test_outdated_defers(self):
        self.assertEqual(corpus_answer_decision("OUTDATED",True),"DEFER_TRUTH_CORRECTION")
    def test_miss_not_answer(self):
        self.assertEqual(corpus_answer_decision("TRUE",False),"MISS")
    def test_unknown_state_fails(self):
        with self.assertRaises(ValueError):corpus_answer_decision("UNKNOWN",True)
    def test_non_bool_hit_rejected(self):
        with self.assertRaises(ValueError):corpus_answer_decision("TRUE",1)
if __name__=="__main__":unittest.main()

import unittest
from unittest.mock import Mock
from grounded_generation_diagnostics_v02338 import CASES,validate_cases,run
class GroundedDiagnosticsTests(unittest.TestCase):
    def test_categories(self):
        self.assertTrue(validate_cases())
        self.assertEqual({c["axis"] for c in CASES},{"copy","extract","transform","completion","counterfactual"})
    def test_duplicates(self):
        with self.assertRaisesRegex(ValueError,"Duplicate"):validate_cases(CASES+[CASES[0]])
    def test_no_training_or_semantic_input(self):
        g=Mock()
        g.generate.return_value={"text":"test","generated_tokens":1,"elapsed_seconds":0.01}
        results=run({"base":g},CASES[:2])
        self.assertEqual(len(results),2)
        for call in g.generate.call_args_list:
            self.assertEqual(call.kwargs["temperature"],0)
        self.assertIsNone(results[0]["outputs"]["base"]["manual_review"]["fidelity"])
    def test_copy_and_counterfactual_pairs(self):
        self.assertEqual([c["id"] for c in CASES if c["axis"]=="copy"],["A1","A2"])
        negatives=[c for c in CASES if c["axis"]=="counterfactual"]
        self.assertEqual(len(negatives),2)
        self.assertNotEqual(negatives[0]["fact"],negatives[1]["fact"])
    def test_gold_prefix_tracked(self):
        completions=[c for c in CASES if c["axis"]=="completion"]
        self.assertEqual(len(completions),2)
        for c in completions:self.assertTrue(c["prompt"].endswith(c["prefix"]))
if __name__=="__main__":unittest.main()

import unittest
from diagnose_recovery_understanding_v02305 import (
    COMMANDS, counterfactual_prompt, candidate_summary, command_preference)
from prepare_prefix_recovery_v02304 import build

class RecoveryDiagnosisTests(unittest.TestCase):
    def test_swap_all_examples(self):
        for row in build():
            other="restart" if row["mode"]=="continue" else "continue"
            swapped=counterfactual_prompt(row["user"],other)
            self.assertIn(COMMANDS[other],swapped)
            self.assertNotIn(COMMANDS[row["mode"]],swapped)
    def test_reversible_swap(self):
        for row in build():
            other="restart" if row["mode"]=="continue" else "continue"
            swapped=counterfactual_prompt(row["user"],other)
            self.assertEqual(counterfactual_prompt(swapped,row["mode"]),row["user"])
    def test_target_win(self):
        r=candidate_summary({"target":1.2,"generic_1":2.1,"generic_2":2.0})
        self.assertTrue(r["target_beats_generic"])
        self.assertAlmostEqual(r["target_vs_generic_margin"],0.8)
    def test_generic_win(self):
        self.assertFalse(candidate_summary({"target":3.0,"generic_1":1.0,"generic_2":1.5})["target_beats_generic"])
    def test_command_delta(self):
        self.assertGreater(command_preference(1.0,1.5),0)
        self.assertLess(command_preference(1.5,1.0),0)
    def test_wrong_prompt_fails(self):
        with self.assertRaises(ValueError):
            counterfactual_prompt("普通の質問","restart")
if __name__=="__main__":unittest.main()

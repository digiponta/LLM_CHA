import unittest
from evaluate_context_sensitivity_v0222 import SCENARIOS,QUESTION,prompt_for,lexical_hits

class ContextSensitivityTests(unittest.TestCase):
    def test_identical_last_question(self):
        for row in SCENARIOS:
            self.assertEqual(prompt_for(row["history"]).splitlines()[-1],"人: "+QUESTION)
    def test_distinct_topics_and_no_context(self):
        prompts=[prompt_for(x["history"]) for x in SCENARIOS]
        self.assertEqual(len(set(prompts)),4)
        self.assertIn("宇宙探査",prompts[0]);self.assertIn("カレー",prompts[1])
        self.assertEqual(prompts[-1],"人: "+QUESTION)
    def test_overlap_is_explicit_not_semantic(self):
        self.assertEqual(lexical_hits("惑星を探査する",["宇宙","探査","惑星"]),["探査","惑星"])
        self.assertEqual(lexical_hits("そうですね",["宇宙","探査"]),[])
if __name__=="__main__":unittest.main()

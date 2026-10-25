import unittest
from response_quality_v094 import evidence_score,best_evidence,generation_quality
from topic_suggestion_followup_v093 import explain_followup

class QualityGateTests(unittest.TestCase):
    def test_reject_fragment(self):
        self.assertLess(evidence_score("エネルギーが、そう。","エネルギー準位"),0)
    def test_find_relevant_energy_level(self):
        text=["エネルギーが、そう。","量子力学で表現可能な動的平衡状態にある系では、外力により１つのエネルギ順位は２つの順位に分裂。"]
        self.assertIn("順位に分裂",best_evidence(text,"エネルギー準位"))
    def test_followup_selects_complete_evidence(self):
        result=explain_followup("2番目の話題を教えて",
                ["粒子と波動","エネルギー準位"],
                "エネルギーが、そう。\n外力により１つのエネルギ順位が分裂する。")
        self.assertEqual(result["route"],"TOPIC_FOLLOWUP_CORPUS")
        self.assertNotIn("エネルギーが、そう。",result["answer"])
    def test_malformed_opinion_rejected(self):
        r=generation_quality("貴方はどう思う？","有希広")
        self.assertFalse(r["accepted"])
        self.assertTrue(r["fallback"])
    def test_normal_opinion_not_forced(self):
        self.assertTrue(generation_quality("貴方はどう思う？","私はその考えには一定の合理性があると思う。")["accepted"])
    def test_ordinary_qa_unaffected(self):
        self.assertTrue(generation_quality("数学とは","数学は構造を研究する学問。")["accepted"])
    def test_no_evidence(self):
        self.assertIsNone(best_evidence(["エネルギーが、そう。"],"エネルギー準位"))
if __name__=="__main__":unittest.main()

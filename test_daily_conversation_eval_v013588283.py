import unittest
from daily_conversation_eval_v013588283 import evaluate,grade

D={"cases":[{"id":"daily-001","question":"今日は何をしてる？"},{"id":"daily-002","question":"今何してる？"}]}
class DailyConversationEvalTests(unittest.TestCase):
    def test_reported_failure(self):
        x=grade("。よれにする言語である六階層のシステム。","未学習です","GATE_REVIEW")
        self.assertTrue(x["candidate_malformed"])
        self.assertTrue(x["fallback"])
        self.assertFalse(x["display_surface_usable"])
    def test_plausible_surface_requires_human_check(self):
        x=grade("今はあなたと話している。","今はあなたと話している。","KNOWN")
        self.assertTrue(x["display_surface_usable"])
        self.assertTrue(x["needs_human_review"])
    def test_no_observation_is_not_success(self):
        x=evaluate(D,{"runs":[]})
        self.assertEqual(x["observed"],0)
        self.assertEqual(x["rows"][0]["status"],"NOT_RUN")
    def test_partial_observation(self):
        x=evaluate(D,{"runs":[{"id":"daily-001","candidate":"。変な文章","display":"未学習です","route":"GATE_REVIEW"}]})
        self.assertEqual((x["observed"],x["fallback"],x["candidate_malformed"]),(1,1,1))
        self.assertFalse(x["model_improvement_claimed"])
    def test_duplicate_rejected(self):
        with self.assertRaises(ValueError):
            evaluate(D,{"runs":[{"id":"daily-001"},{"id":"daily-001"}]})
    def test_unknown_rejected(self):
        with self.assertRaises(ValueError):
            evaluate(D,{"runs":[{"id":"unregistered"}]})
if __name__=="__main__":unittest.main()

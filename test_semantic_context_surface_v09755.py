import unittest
from semantic_context_surface_v09755 import Carryover, evaluation
from preference_intent_v09750 import detect

class ContextSurfaceTests(unittest.TestCase):
    def test_followup(self):
        state=Carryover()
        self.assertIn("スファレライト",state.observe("スファレライトの成分は"))
        answer=state.observe("化学組成を知りたい")
        self.assertIn("スファレライトの化学組成",answer)
    def test_no_fabrication(self):
        state=Carryover()
        state.observe("スファレライトの成分は")
        answer=state.observe("化学組成を知りたい")
        self.assertNotIn("ZnS",answer)
    def test_topic_is_cleared_on_definition(self):
        state=Carryover()
        state.observe("スファレライトの成分は")
        self.assertIsNone(state.observe("スファレライトとは"))
        self.assertIsNone(state.pending_topic)
    def test_preference_particle(self):
        p=detect("宝石としてのスファレライトが好きです")
        self.assertIsNotNone(p)
        self.assertEqual(p.response,"宝石としてのスファレライトが好きなんだね。")
        self.assertNotIn("がが",p.response)
    def test_adjective(self):
        self.assertEqual(evaluation("きれいです"),"そう。")
        self.assertEqual(evaluation("美しいです"),"そう。")
    def test_question_does_not_shortcut(self):
        self.assertIsNone(evaluation("きれいとは"))
    def test_unrelated_not_rewritten(self):
        self.assertIsNone(evaluation("お疲れさま"))
    def test_past_regression(self):
        self.assertEqual(detect("ラテが好き").response,"ラテが好きなんだね。")
if __name__=="__main__": unittest.main()

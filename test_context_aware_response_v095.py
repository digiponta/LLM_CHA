import unittest
from context_aware_response_v095 import ContextualResponse,opinion_request

class ContextResponseTests(unittest.TestCase):
    def test_opinion_intent(self):
        self.assertTrue(opinion_request("貴方はどう思う？"))
    def test_unrelated_definition(self):
        state=ContextualResponse()
        state.set_topic("数学","WIKIPEDIA")
        self.assertIsNone(state.respond("文学とは"))
    def test_missing_context(self):
        self.assertEqual(ContextualResponse().respond("貴方はどう思う？")["route"],
                         "CONTEXT_OPINION_CLARIFICATION")
    def test_wikipedia_topic(self):
        state=ContextualResponse()
        state.set_topic("数学","WIKIPEDIA")
        r=state.respond("貴方はどう思う？")
        self.assertIn("数学",r["answer"])
        self.assertNotIn("有希広",r["answer"])
    def test_corpus_attribution(self):
        state=ContextualResponse()
        state.set_topic("数学","NAGATO_CORPUS",["数学は、文学の分類。"])
        r=state.respond("どう思う？")
        self.assertIn("数学は、文学の分類。",r["answer"])
        self.assertIn("検証されていない",r["answer"])
        self.assertFalse(r["train_ready"])
    def test_reset(self):
        state=ContextualResponse()
        state.set_topic("数学","WIKIPEDIA")
        state.reset()
        self.assertEqual(state.respond("どう思う？")["route"],
                         "CONTEXT_OPINION_CLARIFICATION")
if __name__=="__main__":unittest.main()

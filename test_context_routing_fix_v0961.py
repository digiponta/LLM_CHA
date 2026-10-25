import unittest
from context_aware_response_v095 import ContextualResponse, explicit_opinion_topic
class ContextRoutingFixTests(unittest.TestCase):
    def test_explicit_memory_opinion(self):
        s=ContextualResponse();s.set_topic("量子力学","NAGATO_CORPUS",["原文"])
        r=s.respond("メモリについて貴方はどう思う？")
        self.assertEqual(r["topic"],"メモリ")
        self.assertNotIn("量子力学",r["answer"])
    def test_wikipedia_selection_update(self):
        s=ContextualResponse();s.set_topic("量子力学","NAGATO_CORPUS")
        s.set_topic("メモリ","WIKIPEDIA_SELECTED")
        self.assertEqual(s.respond("貴方はどう思う？")["topic"],"メモリ")
    def test_explicit_extraction(self):
        self.assertEqual(explicit_opinion_topic("メモリについて貴方はどう思う？"),"メモリ")
    def test_ordinary_question_unaffected(self):
        self.assertIsNone(ContextualResponse().respond("メモリとは"))
if __name__=="__main__":unittest.main()

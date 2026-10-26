import tempfile,unittest
from semantic_dialogue_bridge_v0112 import DialogueBridge
from semantic_equivalence_router_v0111 import EquivalenceAssertion

class Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.bridge=DialogueBridge(self.temp.name)
    def tearDown(self):self.temp.cleanup()
    def pair(self, question="物質波とは", a="物質波はドブロイ波", b="物質波は電磁波",context=""):
        return self.bridge.compare(question,a,b,EquivalenceAssertion("DIVERGENT"),context=context)
    def test_ask_review_reuse(self):
        x=self.pair()
        self.assertEqual(x["action"],"ASK_USER")
        self.bridge.review(x["ticket_id"],"prefer_b")
        y=self.pair()
        self.assertEqual(y["action"],"USER_PREFERENCE")
        self.assertEqual(y["answer"],"物質波は電磁波")
        self.assertEqual(y["factual_truth"],"UNVERIFIED")
    def test_different_question_not_reused(self):
        x=self.pair()
        self.bridge.review(x["ticket_id"],"prefer_a")
        self.assertEqual(self.pair(question="別質問")["action"],"ASK_USER")
    def test_different_answer_not_reused(self):
        x=self.pair()
        self.bridge.review(x["ticket_id"],"prefer_a")
        self.assertEqual(self.pair(b="別の主張")["action"],"ASK_USER")
    def test_contextual_refuses_unrelated_context(self):
        x=self.pair()
        self.bridge.review(x["ticket_id"],"both_contextual",context="仮説として")
        self.assertEqual(self.pair(context="仮説として")["action"],"CONTEXT_SPLIT")
        self.assertEqual(self.pair(context="事実として")["action"],"ASK_USER")
    def test_neither_stays_unresolved(self):
        x=self.pair()
        self.bridge.review(x["ticket_id"],"neither")
        self.assertEqual(self.pair()["action"],"UNRESOLVED")
    def test_lexical_does_not_ticket(self):
        x=self.bridge.compare("思考とは","解読／分析","解読/分析")
        self.assertEqual(x["action"],"CANONICALIZED_LEXICAL")
    def test_approved_equivalence_does_not_ticket(self):
        x=self.bridge.compare("q","a","b",
            EquivalenceAssertion("EQUIVALENT","approval-01",True,"canonical"))
        self.assertEqual(x["action"],"CANONICALIZED_APPROVED")
if __name__=="__main__":unittest.main()

import tempfile
import unittest
from dataclasses import dataclass
from chat_semantic_reconciliation_v0119 import get_bridge, prelookup, reconcile

@dataclass
class Candidate:
    hit: bool=True
    answer: str="記憶の回答"
    provenance: str="corpus:unverified"

class ChatIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.bridge=get_bridge(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def test_prelookup_miss(self):
        self.assertIsNone(prelookup(self.bridge,"人類とは","人類","",Candidate(),"UNVERIFIED"))
    def test_review_then_prelookup(self):
        result=reconcile(self.bridge,"人類とは","人類","","生成A",Candidate(),"UNVERIFIED")
        self.assertEqual(result["action"],"ASK_USER")
        self.bridge.review(result["ticket_id"],"prefer_b")
        cached=prelookup(self.bridge,"人類とは","人類","",Candidate(),"UNVERIFIED")
        self.assertEqual(cached["answer"],"記憶の回答")
    def test_blocked_truth_prevents_lookup(self):
        result=reconcile(self.bridge,"人類とは","人類","","生成A",Candidate(),"UNVERIFIED")
        self.bridge.review(result["ticket_id"],"prefer_b")
        self.assertIsNone(prelookup(self.bridge,"人類とは","人類","",Candidate(),"FALSE"))
        self.assertIsNone(reconcile(self.bridge,"人類とは","人類","","生成A",Candidate(),"CONTESTED"))
    def test_quality_invalid_does_not_open_ticket(self):
        r=reconcile(self.bridge,"人類とは","人類","","壊れた�",Candidate(),"UNVERIFIED")
        self.assertEqual(r["action"],"QUALITY_REVIEW")
        self.assertFalse(list(self.bridge.tickets.root.glob("*.json")))
    def test_changed_memory_no_prelookup(self):
        result=reconcile(self.bridge,"人類とは","人類","","生成A",Candidate(),"UNVERIFIED")
        self.bridge.review(result["ticket_id"],"prefer_b")
        self.assertIsNone(prelookup(self.bridge,"人類とは","人類","",
                                    Candidate(answer="更新された記憶"),"UNVERIFIED"))
if __name__=="__main__":unittest.main()

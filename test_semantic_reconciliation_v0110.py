import tempfile
import unittest
from semantic_reconciliation_v0110 import ReconciliationStore, render_question

class ReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.store=ReconciliationStore(self.tmp.name)
    def tearDown(self):
        self.tmp.cleanup()
    def ticket(self,**kwargs):
        return self.store.open("物質波とは","物質波はドブロイ波である","物質波は電磁波である",**kwargs)
    def test_preference_persists_without_truth_promotion(self):
        t=self.ticket()
        updated=self.store.review(t["id"],"prefer_a")
        self.assertEqual(updated["state"],"USER_REVIEWED")
        self.assertEqual(updated["factual_truth"],"UNVERIFIED")
        self.assertEqual(updated["approval_state"],"NOT_APPROVED")
        self.assertEqual(self.store.get(t["id"])["preferred_expression"],"物質波はドブロイ波である")
    def test_review_is_immutable(self):
        t=self.ticket()
        self.store.review(t["id"],"prefer_a")
        with self.assertRaises(ValueError):self.store.review(t["id"],"prefer_b")
    def test_context_required_for_both(self):
        t=self.ticket()
        with self.assertRaises(ValueError):self.store.review(t["id"],"both_contextual")
        r=self.store.review(t["id"],"both_contextual",context="別の物理学上の意味として区別")
        self.assertIsNone(r["preferred_expression"])
    def test_equivalent_surface_rejected(self):
        with self.assertRaises(ValueError):
            self.store.open("質問","解読／分析","解読/分析")
    def test_unknown_requires_review(self):
        t=self.ticket(divergence="UNKNOWN")
        self.assertIn("prefer_a",render_question(t))
        self.assertEqual(self.store.get(t["id"])["state"],"CLARIFICATION_PENDING")
    def test_invalid_ticket_id(self):
        with self.assertRaises(ValueError):self.store.get("../escape")
    def test_evidence_does_not_promote(self):
        t=self.store.open("Q","A","B",evidence_a={"source":"external","verified":False})
        self.assertEqual(t["approval_state"],"NOT_APPROVED")
if __name__=="__main__":unittest.main()

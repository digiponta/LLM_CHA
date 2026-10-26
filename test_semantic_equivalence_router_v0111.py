import tempfile
import unittest
from semantic_equivalence_router_v0111 import EquivalenceAssertion, resolve, choose
from semantic_reconciliation_v0110 import ReconciliationStore

class RouterTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.store=ReconciliationStore(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def run_case(self, assertion=None, a="物質波はドブロイ波である", b="物質波は電磁波である"):
        return resolve("物質波とは",a,b,assertion,store=self.store)
    def test_lexical_nfkc(self):
        x=self.run_case(a="解読／分析",b="解読/分析")
        self.assertEqual(x["action"],"CANONICALIZED_LEXICAL")
    def test_divergent_asks_user(self):
        x=self.run_case(EquivalenceAssertion("DIVERGENT"))
        self.assertEqual(x["action"],"ASK_USER")
        self.assertEqual(self.store.get(x["ticket_id"])["state"],"CLARIFICATION_PENDING")
    def test_unknown_asks_user(self):
        self.assertEqual(self.run_case()["action"],"ASK_USER")
    def test_approved_equivalence_normalizes(self):
        x=self.run_case(EquivalenceAssertion("EQUIVALENT","approval-001",True,
                                             "物質波はドブロイ波である"))
        self.assertEqual(x["action"],"CANONICALIZED_APPROVED")
        self.assertEqual(list(self.store.root.glob("*.json")),[])
    def test_unapproved_equivalence_must_not_merge(self):
        x=self.run_case(EquivalenceAssertion("EQUIVALENT","source-1",False,"代表文"))
        self.assertEqual(x["action"],"ASK_USER")
        self.assertEqual(x["divergence_status"],"UNKNOWN")
    def test_missing_provenance_must_not_merge(self):
        x=self.run_case(EquivalenceAssertion("EQUIVALENT",None,True,"代表文"))
        self.assertEqual(x["action"],"ASK_USER")
    def test_user_choice_not_fact_approval(self):
        x=self.run_case(EquivalenceAssertion("DIVERGENT"))
        y=choose(self.store,x["ticket_id"],"prefer_b")
        self.assertEqual(y["state"],"USER_REVIEWED")
        self.assertEqual(y["factual_truth"],"UNVERIFIED")
        self.assertEqual(y["approval_state"],"NOT_APPROVED")
    def test_bad_status(self):
        with self.assertRaises(ValueError):
            self.run_case(EquivalenceAssertion("CONTRADICTION?"))
if __name__=="__main__":unittest.main()

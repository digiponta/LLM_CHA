import unittest
from dss_unknown_adapter_v023336 import IntegrationResolver,MockDSS,LocalCandidateStore,Assessment

class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.store=LocalCandidateStore();self.r=IntegrationResolver(MockDSS(),self.store)
    def test_propose_confirm_reuse(self):
        self.assertEqual(self.r.receive("昨日の実験の続きをやって","A")["status"],"clarify")
        self.assertEqual(self.r.receive("cursor","A")["status"],"confirm")
        self.assertIsNone(self.store.lookup("A","experiment","target"))
        self.assertEqual(self.r.confirm(True,"A")["status"],"resolved")
        r=self.r.receive("前回の実験の続きをやって","A")
        self.assertEqual(r["value"],"cursor")
    def test_context_scope(self):
        self.r.receive("昨日の実験の続きをやって","A")
        self.r.receive("cursor","A");self.r.confirm(True,"A")
        self.assertEqual(self.r.receive("昨日の実験の続きをやって","B")["status"],"clarify")
    def test_expired_confirmation(self):
        self.r=IntegrationResolver(MockDSS(),self.store,ttl_turns=2)
        self.r.receive("昨日の実験の続きをやって","A")
        self.r.receive("cursor","A")
        self.assertEqual(self.r.confirm(True,"A")["status"],"resolved")
        # stale candidate from a different context must be rejected
        self.r.receive("昨日の実験の続きをやって","B")
        self.r.receive("cursor","B")
        self.assertEqual(self.r.confirm(True,"C")["status"],"expired")
        self.assertIsNone(self.store.lookup("B","experiment","target"))
    def test_reject_and_invalidate(self):
        self.r.receive("昨日の実験の続きをやって","A")
        self.r.receive("cursor","A")
        self.assertEqual(self.r.confirm(False,"A")["status"],"rejected")
        self.assertIsNone(self.store.lookup("A","experiment","target"))
        self.r.receive("昨日の実験の続きをやって","A")
        self.r.receive("semantic_memory","A");self.r.confirm(True,"A")
        self.r.invalidate("A","experiment","target")
        self.assertIsNone(self.store.lookup("A","experiment","target"))
    def test_bounded_unknown(self):
        self.r.receive("昨日の実験の続きをやって","A")
        self.assertEqual(self.r.receive("不明","A")["status"],"clarify")
        self.assertEqual(self.r.receive("わからない","A")["status"],"abstain")
        self.assertFalse(self.store.records)
    def test_external_dss_contract(self):
        def assessor(text,ctx):return Assessment("unknown","document","selection",
                      "どれですか？",("first","second"))
        r=IntegrationResolver(assessor,LocalCandidateStore())
        self.assertEqual(r.receive("再開","scope")["status"],"clarify")
        self.assertEqual(r.receive("first","scope")["status"],"confirm")
    def test_do_not_confuse_unknown_tokens(self):
        self.assertEqual(self.r.receive("XYZ 未知トークン列","A")["status"],"known")
        self.assertIsNone(self.r.pending)
if __name__=="__main__":unittest.main()

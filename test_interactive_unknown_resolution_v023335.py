import unittest
from interactive_unknown_resolution_v023335 import Resolver,MemoryAdapter
class UnknownResolutionTests(unittest.TestCase):
    def test_clarify_and_confirm(self):
        r=Resolver()
        self.assertEqual(r.receive("昨日の実験の続きをやって")["status"],"clarify")
        self.assertEqual(r.receive("Cursorの方")["status"],"confirm")
        self.assertEqual(len(r.store.approved),0)
        self.assertEqual(r.confirm(True)["status"],"resolved")
        self.assertEqual(r.receive("昨日の実験の続きをやって")["status"],"resolved")
    def test_rejection_no_promotion(self):
        r=Resolver()
        r.receive("前回の実験の続きをやって")
        r.receive("Semantic Memory")
        self.assertEqual(r.confirm(False)["status"],"rejected")
        self.assertFalse(r.store.approved)
    def test_no_unverified_save(self):
        r=Resolver()
        r.receive("昨日の実験の続きをやって")
        self.assertEqual(r.receive("よく分からない")["status"],"clarify")
        self.assertEqual(r.receive("分からない")["status"],"abstain")
        self.assertFalse(r.store.approved)
    def test_cancel(self):
        r=Resolver()
        r.receive("昨日の実験の続きをやって")
        self.assertEqual(r.receive("キャンセル")["status"],"cancelled")
        self.assertFalse(r.state.waiting())
    def test_unknown_vs_unknown_token(self):
        r=Resolver()
        self.assertEqual(r.receive("任意の未知トークン列")["status"],"unhandled")
        self.assertFalse(r.store.approved)
    def test_existing_memory_no_repeat_question(self):
        r=Resolver()
        r.receive("昨日の実験の続きをやって")
        r.receive("カーソル")
        r.confirm(True)
        self.assertEqual(r.receive("前回の実験の続きをやって")["value"],"cursor")
if __name__=="__main__":unittest.main()

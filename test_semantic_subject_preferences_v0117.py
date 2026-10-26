import tempfile
import unittest
from semantic_subject_preferences_v0117 import SubjectPreferenceBridge
from semantic_equivalence_router_v0111 import EquivalenceAssertion

class SubjectPreferenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.b=SubjectPreferenceBridge(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def compare(self,a="生成A", b="記憶B",q="人類とは",subject="人類",context=""):
        return self.b.compare(q,a,b,EquivalenceAssertion("UNKNOWN"),subject=subject,context=context)
    def test_reuse_changed_a(self):
        t=self.compare()
        self.b.review(t["ticket_id"],"prefer_b")
        r=self.compare(a="新しく異なる生成回答")
        self.assertEqual(r["action"],"USER_PREFERENCE")
        self.assertEqual(r["answer"],"記憶B")
        self.assertEqual(r["ticket_id"],t["ticket_id"])
    def test_memory_changed_asks_again(self):
        t=self.compare()
        self.b.review(t["ticket_id"],"prefer_b")
        self.assertEqual(self.compare(a="別生成",b="更新済み記憶")["action"],"ASK_USER")
    def test_question_changed_asks_again(self):
        t=self.compare()
        self.b.review(t["ticket_id"],"prefer_b")
        self.assertEqual(self.compare(q="人類とは何か")["action"],"ASK_USER")
    def test_subject_changed_asks_again(self):
        t=self.compare()
        self.b.review(t["ticket_id"],"prefer_b")
        self.assertEqual(self.compare(subject="生命")["action"],"ASK_USER")
    def test_context_changed_asks_again(self):
        t=self.compare()
        self.b.review(t["ticket_id"],"prefer_b")
        self.assertEqual(self.compare(context="別の文脈")["action"],"ASK_USER")
    def test_prefer_a_not_reused_when_a_changes(self):
        t=self.compare()
        self.b.review(t["ticket_id"],"prefer_a")
        self.assertEqual(self.compare(a="異なる生成文")["action"],"ASK_USER")
    def test_no_truth_promotion(self):
        t=self.compare()
        self.b.review(t["ticket_id"],"prefer_b")
        r=self.compare(a="異なる生成文")
        self.assertEqual(r["factual_truth"],"UNVERIFIED")
if __name__=="__main__":unittest.main()

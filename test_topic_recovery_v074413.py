import unittest
from topic_recovery_v074413 import resolve

class TopicRecoveryTests(unittest.TestCase):
    def test_alias(self):
        r=resolve("量子重ね合わせについて教えて")
        self.assertEqual((r.status,r.query),("NORMALIZED","重ね合わせについて教えて"))
    def test_unrelated_query_unchanged(self):
        self.assertEqual(resolve("GPUとは").status,"UNCHANGED")
    def test_followup_with_evidence(self):
        self.assertEqual(resolve("もう少し詳しく","宇宙",True).status,"FOLLOWUP_EVIDENCE")
    def test_followup_without_evidence(self):
        self.assertEqual(resolve("もう少し詳しく","宇宙",False).status,"NO_NEW_EVIDENCE")
    def test_followup_without_topic(self):
        self.assertEqual(resolve("もっと詳しく").status,"CLARIFY")
    def test_command_not_modified(self):
        self.assertEqual(resolve("/sleep").status,"UNCHANGED")

if __name__=="__main__":
    unittest.main()

import unittest
from japanese_dialogue_audit_v074440 import audit,audit_dialogue

class AuditTests(unittest.TestCase):
    def test_topic_lost(self):
        self.assertIn("TOPIC_LOST",audit("もっと詳しく","長門有希。","量子力学")["flags"])
    def test_legitimate_identity(self):
        self.assertFalse(audit("あなたは誰ですか","長門有希。")["review"])
    def test_failed_generation(self):
        self.assertIn("GENERATION_FAILURE",audit("数式の意味","回答をうまく生成できませんでした。")["flags"])
    def test_grounded_answer(self):
        self.assertFalse(audit("量子ビットとは","Wikipediaによると、量子ビットは基本単位である。")["review"])
    def test_context(self):
        result=audit_dialogue([{"question":"量子力学とは","answer":"定義。"},{"question":"もっと詳しく","answer":"長門有希。"}])
        self.assertEqual(result["flagged"],1)
if __name__=="__main__": unittest.main()

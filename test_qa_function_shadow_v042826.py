import unittest
from qa_function_shadow_v042826 import assess,report

class Tests(unittest.TestCase):
    def test_greeting(self):
        self.assertEqual(assess("こんにちは。","こんにちは。")[0],"SUPPORTED")
    def test_identity(self):
        self.assertEqual(assess("あなたは誰ですか？","長門有希。")[0],"SUPPORTED")
    def test_gpu(self):
        self.assertEqual(assess("GPUって何？","GPUは並列演算を行う処理装置。")[0],"SUPPORTED")
    def test_uninformative_unknown(self):
        self.assertEqual(assess("GPUとは何ですか？","未学習です")[0],"REVIEW_CANDIDATE")
    def test_unknown_can_be_contextually_correct(self):
        self.assertEqual(assess("昨日買った本の題名を教えて","未学習です")[0],"REVIEW_CANDIDATE")
    def test_unhandled_abstains(self):
        self.assertEqual(assess("眠くなってきた。","無頼な名前は、独立した。")[0],"ABSTAIN")
    def test_no_blank_false_confidence(self):
        self.assertEqual(assess("","")[0],"ABSTAIN")
if __name__=="__main__":unittest.main()

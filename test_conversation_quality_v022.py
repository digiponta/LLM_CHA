import unittest
from conversation_quality_gate_v022 import quality_check

class ConversationQualityTests(unittest.TestCase):
    def check(self,q,a,lex=0.5,sem=0.9):
        return quality_check(q,a,lexical_agreement=lex,semantic_agreement=sem)
    def test_thanks_mismatch(self):
        self.assertFalse(self.check("ありがとう","お疲れさまです")[0])
    def test_thanks_correct(self):
        self.assertTrue(self.check("ありがとう","どういたしまして。")[0])
    def test_fatigue_mismatch(self):
        self.assertFalse(self.check("今日は少し疲れました","お疲れました")[0])
    def test_story_mismatch(self):
        self.assertFalse(self.check("何か面白い話をして","いいですね")[0])
    def test_book_question_mismatch(self):
        self.assertFalse(self.check("どんな本が好き？","いいですね")[0])
    def test_semantic_rescue_low_lexical(self):
        self.assertFalse(self.check("GPUはなぜ高速なの？","GPUはいえ、何を並列に処理するの並列計算を効率よく処理できることです。",0.09,0.932)[0])
    def test_identity_answer(self):
        self.assertTrue(self.check("あなたは誰ですか","長門有希。",1,1)[0])
    def test_unknown_not_intercepted(self):
        self.assertTrue(self.check("CPUとは","CPUは中央処理装置です。",0.6,0.9)[0])
if __name__=="__main__":unittest.main()

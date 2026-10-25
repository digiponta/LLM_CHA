import unittest
from unittest.mock import patch
from types import SimpleNamespace
import chat

def result(text):
    return SimpleNamespace(text=text,mean_confidence=0.286,
                           min_confidence=0.070,mean_top2_margin=0.165)
class ExtremeDisagreementTests(unittest.TestCase):
    def call_gate(self,agreement,semantic):
        samples=[result("通常の日本語回答です。"),result("別の回答です。")]
        with patch.object(chat,"mean_pairwise_agreement",return_value=agreement),patch.object(
            chat,"mean_pairwise_semantic_agreement",return_value=semantic):
            return chat.evaluate_unknown_gate(None,None,samples,
                min_confidence=0.18,min_token_confidence=0.02,
                min_mean_margin=0.01,min_agreement=0.35,
                min_semantic_agreement=0.82,allow_semantic_rescue=True)
    def test_extreme_disagreement_rejected(self):
        decision=self.call_gate(0.017,0.854)
        self.assertFalse(decision[0])
        self.assertEqual(decision[4],"extreme lexical probe disagreement")
    def test_semantic_rescue_still_possible_above_floor(self):
        decision=self.call_gate(0.12,0.854)
        self.assertTrue(decision[0])
    def test_lexical_accept_unaffected(self):
        self.assertTrue(self.call_gate(0.42,0.70)[0])
if __name__=="__main__":unittest.main()

import unittest
from structured_semantic_purpose_v02315 import extract,action_for
class StructuredPurposeTests(unittest.TestCase):
    def test_sequential(self):
        s=extract("LLMを勉強してから開発したい")
        self.assertEqual(s.topic,"LLM")
        self.assertEqual(s.purposes,["learning","development"])
        self.assertEqual(s.relation,"SEQUENTIAL")
        self.assertEqual(action_for(s),"HANDOFF")
    def test_preference(self):
        s=extract("Pythonは開発じゃなく勉強したい")
        self.assertEqual(s.purposes,["learning"])
        self.assertEqual(s.polarity,"NEGATED_ALTERNATIVE")
        self.assertEqual(s.relation,"PREFERENCE")
    def test_ambiguous(self):
        s=extract("Pythonに興味がある")
        self.assertEqual(action_for(s),"ASK_CONFIRMATION")
    def test_clear(self):
        s=extract("Pythonでアプリを開発したい")
        self.assertEqual(s.purposes,["development"])
        self.assertEqual(action_for(s),"HANDOFF")
    def test_no_evidence(self):
        s=extract("123456789")
        self.assertEqual(action_for(s),"ASK_CLARIFICATION")
    def test_evidence(self):
        s=extract("画像認識のエラーを直したい")
        self.assertEqual(s.purposes,["troubleshooting"])
        self.assertIn("vector_candidate",s.evidence)
if __name__=="__main__":unittest.main()

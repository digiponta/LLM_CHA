import unittest
from evidence_dialogue_policy_v02318 import decide,compare
class EvidencePolicyTests(unittest.TestCase):
    def test_natural_question(self):
        d=decide("Pythonに興味がある")
        self.assertEqual(d.action,"ASK_CONFIRMATION")
        self.assertNotIn("casual",d.question)
        self.assertIn("雑談",d.question)
    def test_parser_development_miss(self):
        self.assertEqual(decide("Pythonでアプリを組み上げたい").action,"HANDOFF")
    def test_parser_troubleshoot_miss(self):
        self.assertEqual(decide("LLMの出力がおかしい").action,"HANDOFF")
    def test_casual(self):
        self.assertEqual(decide("Pythonについて雑談したい").action,"RESPOND")
    def test_multi(self):
        self.assertEqual(decide("LLMを勉強して開発もしたい").action,"PLAN")
    def test_ambiguous(self):
        self.assertEqual(decide("LLMに興味がある").action,"ASK_CONFIRMATION")
    def test_unknown(self):
        self.assertEqual(decide("12345678").action,"ASK_CLARIFICATION")
    def test_negation(self):
        d=decide("Pythonは開発じゃなく勉強したい")
        self.assertEqual((d.action,d.purposes),("HANDOFF",["learning"]))
    def test_trace(self):
        r=compare("LLMを勉強したい")
        self.assertIn("parser_status",r)
        self.assertIn("decision",r)
if __name__=="__main__":unittest.main()

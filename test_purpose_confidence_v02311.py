import unittest
from purpose_confidence_v02311 import DSS,respond,explicit_goal
class PurposeConfidenceTests(unittest.TestCase):
    def test_ambiguous(self):
        d,action,_=respond(DSS(),"Pythonを試したい")
        self.assertEqual((d.state,action),("CONFIRMING","ASK_CONFIRMATION"))
    def test_yes(self):
        d,_,_=respond(DSS(),"Pythonを試したい")
        d,action,_=respond(d,"はい")
        self.assertEqual((d.state,action,d.purpose),("EXECUTING","HANDOFF","learning"))
    def test_no(self):
        d,_,_=respond(DSS(),"Pythonを試したい")
        d,action,_=respond(d,"違います")
        self.assertEqual((d.state,action),("DISCOVERING","ASK_CLARIFICATION"))
        self.assertEqual(d.last_rejected_purpose,"learning")
    def test_direct(self):
        d,action,_=respond(DSS(),"Pythonの文法を勉強したい")
        self.assertEqual((action,d.purpose),("HANDOFF","learning"))
    def test_negation(self):
        self.assertEqual(explicit_goal("開発ではなく学習したい")[0],"learning")
        self.assertEqual(explicit_goal("学習ではなく開発したい")[0],"development")
    def test_ai(self):
        d,action,_=respond(DSS(),"AIを作りたい")
        self.assertEqual((action,d.missing),("ASK_CLARIFICATION",["development_target"]))
        d,action,_=respond(d,"LLMを自作したい")
        self.assertEqual(action,"HANDOFF")
    def test_switch(self):
        d,_,_=respond(DSS(),"LLMを自作したい")
        d,action,_=respond(d,"やっぱり画像認識を作りたい")
        self.assertEqual((d.topic,action),("画像認識","HANDOFF"))
    def test_casual(self):
        d,action,_=respond(DSS(),"少し雑談したい")
        self.assertEqual((d.purpose,action),("casual","RESPOND"))
    def test_repetition(self):
        d,_,a=respond(DSS(),"Pythonを触っている")
        d,_,b=respond(d,"そうだね")
        self.assertNotEqual(a,b)
    def test_question_reset(self):
        d,_,_=respond(DSS(),"Pythonを触っている")
        d,_,_=respond(d,"勉強したい")
        self.assertIsNone(d.last_question)
    def test_confidence_label(self):
        d,_,_=respond(DSS(),"Pythonの使い方を知りたい")
        self.assertEqual(d.confidence_kind,"heuristic_not_calibrated")
if __name__=="__main__":unittest.main()

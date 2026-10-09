import unittest
from evidence_dialogue_state_v02319 import DialogueState,step

class DialogueStateTests(unittest.TestCase):
    def test_confirm_yes(self):
        d,action,_=step(DialogueState(),"Pythonに興味がある")
        self.assertEqual(action,"ASK_CONFIRMATION")
        d,action,_=step(d,"はい")
        self.assertEqual((action,d.purposes),("RESPOND",["casual"]))
    def test_confirm_no_then_correction(self):
        d,_,_=step(DialogueState(),"Pythonに興味がある")
        d,action,_=step(d,"いいえ")
        self.assertEqual(action,"ASK_CLARIFICATION")
        self.assertIn("casual",d.rejected)
        d,action,_=step(d,"Pythonを勉強したい")
        self.assertEqual((action,d.purposes),("HANDOFF",["learning"]))
    def test_multiple_purposes(self):
        d,action,_=step(DialogueState(),"LLMを勉強してから開発したい")
        self.assertEqual(action,"PLAN")
        self.assertEqual(d.purposes,["learning","development"])
        self.assertEqual(d.relation,"SEQUENTIAL")
    def test_switch(self):
        d,_,_=step(DialogueState(),"LLMを勉強したい")
        d,action,_=step(d,"やっぱり画像認識を開発したい")
        self.assertEqual((action,d.topic,d.purposes),("HANDOFF","画像認識",["development"]))
    def test_casual(self):
        d,action,reply=step(DialogueState(),"Pythonについて雑談したい")
        self.assertEqual(action,"RESPOND")
        self.assertIn("どんな話",reply)
    def test_question_repeat(self):
        d,_,first=step(DialogueState(),"Pythonのこと")
        d,_,second=step(d,"Pythonのこと")
        self.assertNotEqual(first,second)
    def test_history(self):
        d,_,_=step(DialogueState(),"LLMを勉強したい")
        self.assertEqual(len(d.history),1)
        self.assertEqual(d.turns,1)
    def test_clear_handoff(self):
        d,_,_=step(DialogueState(),"LLMを勉強したい")
        self.assertIsNone(d.last_question)
if __name__=="__main__":unittest.main()

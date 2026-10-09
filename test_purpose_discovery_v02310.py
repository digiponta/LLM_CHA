import unittest
from purpose_discovery_v02310 import DialogueSemanticState,respond,snapshot

class PurposeDiscoveryTests(unittest.TestCase):
    def test_initial_unknown(self):
        d=DialogueSemanticState()
        self.assertEqual(d.state,"UNKNOWN")
        self.assertIn("user_goal",d.missing)
    def test_discover_goal(self):
        d,act,msg=respond(DialogueSemanticState(),"最近、Pythonを触っているんだけど")
        self.assertEqual((d.state,act),("DISCOVERING","ASK_CLARIFICATION"))
        self.assertIn("Python",msg)
    def test_multi_candidate_development(self):
        d,act,msg=respond(DialogueSemanticState(),"AIを作りたい")
        self.assertEqual((d.state,act),("DISCOVERING","ASK_CLARIFICATION"))
        self.assertIn("development_target",d.missing)
        self.assertIn("画像認識",msg)
    def test_ready_then_execute(self):
        d,act,msg=respond(DialogueSemanticState(),"LLMを自作したい")
        self.assertEqual((d.state,act),("EXECUTING","HANDOFF"))
        self.assertEqual(d.purpose,"development")
    def test_multi_turn(self):
        d=DialogueSemanticState()
        d,_,_=respond(d,"Pythonを触っている")
        d,_,_=respond(d,"AIを作りたい")
        d,act,_=respond(d,"小さなLLMを自作したい")
        self.assertEqual(act,"HANDOFF")
        self.assertEqual(d.topic,"LLM")
        self.assertEqual(d.turns,3)
    def test_switch(self):
        d=DialogueSemanticState()
        d,_,_=respond(d,"LLMを自作したい")
        d,act,_=respond(d,"やっぱり画像認識を作りたい")
        self.assertEqual(d.topic,"画像認識")
        self.assertEqual(d.purpose,"development")
        self.assertEqual(act,"HANDOFF")
    def test_casual_is_valid_goal(self):
        d,act,msg=respond(DialogueSemanticState(),"少し雑談したい")
        self.assertEqual(d.purpose,"casual")
        self.assertEqual(act,"RESPOND")
    def test_repeated_clarification(self):
        d=DialogueSemanticState()
        d,_,first=respond(d,"Pythonを触っている")
        d,_,second=respond(d,"うん")
        self.assertNotEqual(first,second)
    def test_snapshot(self):
        d=DialogueSemanticState()
        self.assertEqual(snapshot(d)["state"],"UNKNOWN")
if __name__=="__main__":unittest.main()

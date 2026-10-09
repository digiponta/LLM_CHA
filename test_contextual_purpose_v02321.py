import unittest
from evidence_dialogue_state_v02319 import DialogueState
from contextual_purpose_composition_v02321 import step,resolve,generation_context
from evaluate_contextual_purpose_v02321 import evaluate,FRESH
from multiturn_purpose_holdout_v02320 import fixture
class ContextualPurposeTests(unittest.TestCase):
    def test_pronoun_reference(self):
        d=DialogueState()
        d,_,_=step(d,"Pythonを勉強したい")
        d,action,_=step(d,"それを作ってみたい")
        self.assertEqual((action,d.topic,d.purposes),("HANDOFF","Python",["development"]))
    def test_incremental_plan(self):
        d=DialogueState()
        d,_,_=step(d,"LLMを勉強したい")
        d,action,_=step(d,"それから開発もしたい")
        self.assertEqual((action,d.purposes,d.relation),
                         ("PLAN",["learning","development"],"SEQUENTIAL"))
    def test_no_unanchored_reference(self):
        self.assertFalse(resolve(DialogueState(),"それを作りたい")["used_prior_topic"])
    def test_switch(self):
        d=DialogueState()
        d,_,_=step(d,"LLMを勉強したい")
        d,action,_=step(d,"やっぱり画像認識を開発したい")
        self.assertEqual((action,d.topic,d.purposes),("HANDOFF","画像認識",["development"]))
    def test_generation_boundary(self):
        d=DialogueState()
        d,action,_=step(d,"LLMを勉強したい")
        context=generation_context(d,action,"LLMを勉強したい")
        self.assertEqual(context["topic"],"LLM")
        self.assertTrue(context["requires_generation"])
    def test_evaluator_structure(self):
        self.assertEqual(len(evaluate(fixture(),step)),12)
        self.assertEqual(len(evaluate(FRESH,step)),6)
if __name__=="__main__":unittest.main()

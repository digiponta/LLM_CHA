import unittest
from semantic_intent_normalizer_v02313 import normalize,respond
from purpose_confidence_v02311 import DSS
from purpose_fresh_holdout_v02313 import fixture,FRESH_SEQUENCES
from evaluate_semantic_intent_v02313 import evaluate_single,evaluate_multi
class NormalizationTests(unittest.TestCase):
    def test_learning_paraphrase(self):
        text,rules=normalize("Pythonの基礎を習得したい")
        self.assertIn("勉強したい",text)
        self.assertIn("learn-master",rules)
    def test_troubleshooting(self):
        self.assertIn("エラー",normalize("Pythonでバグを見つけた")[0])
    def test_ambiguous(self):
        d,action,_,trace=respond(DSS(),"Pythonを試してみたい")
        self.assertEqual(action,"ASK_CONFIRMATION")
        self.assertEqual(d.state,"CONFIRMING")
    def test_negated_preference(self):
        d,action,_,_=respond(DSS(),"LLMは学習より実装をやりたい")
        self.assertEqual((d.purpose,action),("development","HANDOFF"))
    def test_new_goal_no_extra_question(self):
        d,action,_,_=respond(DSS(),"Pythonの基礎を習得したい")
        self.assertEqual((d.purpose,action),("learning","HANDOFF"))
    def test_old_controller_unmodified(self):
        self.assertEqual(normalize("LLMを自作したい")[0],"LLMを自作したい")
    def test_fresh_fixture_is_separate(self):
        ids={r["id"] for r in fixture()}
        self.assertEqual(len(ids),12)
        self.assertTrue(all(i.startswith("fresh-") for i in ids))
    def test_eval_shapes(self):
        result=evaluate_single(fixture(),respond)
        self.assertEqual(len(result),12)
        self.assertTrue(all("trace" in r for r in result))
    def test_multi_shapes(self):
        result=evaluate_multi(FRESH_SEQUENCES,respond)
        self.assertEqual(len(result),2)
if __name__=="__main__":unittest.main()

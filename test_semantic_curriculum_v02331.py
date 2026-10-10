import unittest,torch
from model import LanguageModel
from train_semantic_curriculum_v02331 import masked_lm,learning_objective,stage_for
from evaluate_semantic_curriculum_v02331 import evaluate
from unittest.mock import Mock

class CurriculumTests(unittest.TestCase):
    def setUp(self):
        self.model=LanguageModel(vocab_size=64,d_model=16,num_layers=1,hidden_dim=32,num_heads=2,context_length=128)
        self.sample=([1,8,9],[14,15,16,2])
    def test_stages(self):
        self.assertEqual([stage_for(i,10) for i in (0,3,7)],["initiation","continuation","full"])
    def test_masked_range(self):
        dev=torch.device("cpu")
        for start,stop in ((0,1),(1,3),(0,None)):
            result=masked_lm(self.model,*self.sample,dev,start,stop)
            self.assertTrue(torch.isfinite(result))
    def test_invalid_range(self):
        with self.assertRaises(ValueError):masked_lm(self.model,*self.sample,torch.device("cpu"),3,2)
    def test_curriculum_objectives(self):
        for stage in ("baseline","initiation","continuation","full"):
            loss=learning_objective(self.model,self.sample,stage,torch.device("cpu"))
            self.assertTrue(torch.isfinite(loss).item())
            loss.backward()
            self.model.zero_grad(set_to_none=True)
    def test_eval_same_budget(self):
        models={k:Mock() for k in ("base","baseline","curriculum")}
        for model in models.values():model.generate.return_value={"text":"ok"}
        rows=evaluate(models,[{"kind":"unseen","user":"LLMを学びたい","topic":"LLM",
                               "purpose":"learning"}],max_new_tokens=17)
        self.assertEqual(len(rows),1)
        for model in models.values():
            self.assertEqual(model.generate.call_count,2)
            self.assertTrue(all(c.kwargs["max_new_tokens"]==17 and c.kwargs["temperature"]==0 for c in model.generate.call_args_list))

if __name__=="__main__":unittest.main()

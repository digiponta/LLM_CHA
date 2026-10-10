import unittest,torch
from model import LanguageModel
from cursor_generalization_v023332 import (
    TASKS,instruction_actions,action_position,ConditionalCursor,
    generate,evaluate,make_data
)
class CursorGeneralizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.manual_seed(332)
        cls.model=LanguageModel(vocab_size=120,d_model=16,num_layers=2,hidden_dim=32,
            num_heads=2,causal=True,context_length=80,use_position_embedding=True).eval()
        for p in cls.model.parameters():p.requires_grad_(False)
    def test_rules_decode(self):
        for task in TASKS:
            for n in (2,3,6,8):
                actions,positions=instruction_actions(task,n)
                cursor=-1;observed=[]
                for a in actions[:-1]:
                    cursor=action_position(cursor,a,n)
                    observed.append(cursor)
                self.assertEqual(observed,positions)
                self.assertEqual(actions[-1],3)
    def test_expected_patterns(self):
        self.assertEqual(instruction_actions("identity",4)[1],[0,1,2,3])
        self.assertEqual(instruction_actions("selective",5)[1],[0,2,4])
        self.assertEqual(instruction_actions("repeat",3)[1],[0,0,1,1,2,2])
        self.assertEqual(instruction_actions("prefix",5)[1],[0,1,2])
        self.assertEqual(instruction_actions("mixed",5)[1],[0,0,2,2,4,4])
    def test_splits_disjoint(self):
        data=make_data(42,list(range(8,72)),list(range(72,88)),12,6,6)
        groups={}
        for key,cases in data.items():
            groups[key]={tuple(s) for t,s in cases}
            self.assertEqual(len(cases),len(groups[key])*len(TASKS))
        for x in ("train","validation","test"):
            for y in ("train","validation","test"):
                if x!=y:self.assertFalse(groups[x]&groups[y])
    def test_gradient_freeze(self):
        head=ConditionalCursor(16)
        head.loss_for(self.model,[10,11],"repeat",7,2,3).backward()
        self.assertTrue(any(p.grad is not None and p.grad.abs().sum()>0 for p in head.parameters()))
        self.assertTrue(all(p.grad is None for p in self.model.parameters()))
    def test_prediction_report(self):
        head=ConditionalCursor(16).eval()
        row=generate(self.model,head,[10,11],"mixed",7,2,3,budget=8)
        self.assertLessEqual(len(row["output"]),8)
        result=evaluate(self.model,head,[("mixed",[10,11])],7,2,3)
        self.assertEqual(result["total"],1)
        self.assertTrue(0<=result["action_prefix_accuracy"]<=1)
if __name__=="__main__":unittest.main()

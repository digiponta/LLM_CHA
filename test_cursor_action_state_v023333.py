import unittest,torch
from model import LanguageModel
from cursor_action_state_v023333 import StatefulCursor,MODES,generate,evaluate
from cursor_generalization_v023332 import instruction_actions

class ActionStateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.manual_seed(333)
        cls.model=LanguageModel(vocab_size=120,d_model=16,num_layers=2,hidden_dim=32,
            num_heads=2,causal=True,context_length=80,use_position_embedding=True).eval()
        for p in cls.model.parameters():p.requires_grad_(False)
    def test_shapes(self):
        for mode in MODES:
            head=StatefulCursor(16,mode)
            scores=head.logits(self.model,[10,11,12],[10],"repeat",0,7,2,0,0)
            self.assertEqual(tuple(scores.shape),(4,))
    def test_head_gradient_only(self):
        for mode in MODES:
            head=StatefulCursor(16,mode)
            head.loss_for(self.model,[10,11,12],"mixed",7,2,3).backward()
            self.assertTrue(any(p.grad is not None and p.grad.abs().sum()>0 for p in head.parameters()))
        self.assertTrue(all(p.grad is None for p in self.model.parameters()))
    def test_generated_history(self):
        for mode in MODES:
            result=generate(self.model,StatefulCursor(16,mode),[10,11],"repeat",7,2,3,budget=10)
            self.assertEqual(len(result["output"]),len(result["actions"]))
            self.assertTrue(set(result["output"])<={10,11,3})
    def test_state_affects_logits(self):
        head=StatefulCursor(16,"transition_state")
        a=head.logits(self.model,[10,11,12],[10,10],"repeat",0,7,2,1,1)
        b=head.logits(self.model,[10,11,12],[10,10],"repeat",0,7,2,0,0)
        self.assertFalse(torch.allclose(a,b))
    def test_reporting(self):
        head=StatefulCursor(16,"baseline")
        rows=[("identity",[10,11]),("repeat",[10,11]),("mixed",[10,11])]
        r=evaluate(self.model,head,rows,7,2,3)
        self.assertEqual(r["overall"]["total"],3)
        self.assertEqual(r["by_task"]["repeat"]["total"],1)
        self.assertEqual(sum(r["by_task"]["identity"]["first_action_error"].values()),1)
if __name__=="__main__":unittest.main()

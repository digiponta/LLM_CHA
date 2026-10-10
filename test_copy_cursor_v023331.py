import unittest,torch
from model import LanguageModel
from copy_cursor_v023331 import CursorHead,decode_cursor,score
class CursorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.manual_seed(331)
        cls.model=LanguageModel(vocab_size=120,d_model=16,num_layers=2,hidden_dim=32,
            num_heads=2,causal=True,context_length=80,use_position_embedding=True).eval()
        for p in cls.model.parameters():p.requires_grad_(False)
    def test_deterministic_cursor_ceiling(self):
        for seq in ([10],[10,11],[10,10,12],[20]*12):
            out=decode_cursor(self.model,None,seq,7,2,3)
            self.assertTrue(out["exact"])
            self.assertEqual(out["positions"],list(range(len(seq)))+[len(seq)])
    def test_learned_actions_shape(self):
        for mode in ("learned","cursor_pointer"):
            head=CursorHead(16,mode)
            a,p=head.step_logits(self.model,[10,11],[], -1,7,2)
            self.assertEqual(tuple(a.shape),(4,))
            if mode=="learned":self.assertIsNone(p)
            else:self.assertEqual(tuple(p.shape),(3,))
    def test_gradient_only_head(self):
        for mode in ("learned","cursor_pointer"):
            head=CursorHead(16,mode)
            loss=head.loss_for(self.model,[10,11],7,2,3)
            loss.backward()
            self.assertTrue(any(p.grad is not None and p.grad.abs().sum()>0 for p in head.parameters()))
        self.assertTrue(all(p.grad is None for p in self.model.parameters()))
    def test_free_prediction_shape(self):
        for mode in ("learned","cursor_pointer"):
            head=CursorHead(16,mode)
            result=decode_cursor(self.model,head,[10,11,12],7,2,3,budget=8)
            self.assertLessEqual(len(result["output"]),8)
            self.assertEqual(len(result["positions"]),len(result["output"]))
    def test_eos_partition(self):
        head=CursorHead(16,"learned")
        r=score(self.model,head,[[10,11],[11,10]],7,2,3)
        self.assertEqual(sum(r["eos"].values()),2)
if __name__=="__main__":unittest.main()

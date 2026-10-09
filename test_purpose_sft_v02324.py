import unittest
import torch
from prepare_purpose_sft_v02324 import build,validate,REPLAY,prompt
from train_purpose_sft_v02324 import encode_row,loss_rows
from model import LanguageModel

class TinyTokenizer:
    eos_id=2
    def encode(self,text,add_bos=False,add_eos=False):
        out=[(ord(ch)%70)+3 for ch in text]
        return ([1] if add_bos else [])+out+([2] if add_eos else [])

class PurposeSFTTests(unittest.TestCase):
    def test_split(self):
        rows=build()
        counts=validate(rows)["counts"]
        self.assertEqual(counts,{"train":36,"val":18,"test":18})
    def test_short_prompt(self):
        p=prompt("Python","learning","Pythonを勉強したい")
        self.assertIn("目的: 学習",p)
        self.assertTrue(p.endswith("AI: "))
    def test_answer_only_mask(self):
        row=build()["train"][0]
        tok=TinyTokenizer()
        x,y=encode_row(tok,row,512)
        prompt_size=len(tok.encode(row["prompt"],add_bos=True))
        self.assertEqual(int((y==-100).sum()),prompt_size-1)
        self.assertEqual(y[-1].item(),tok.eos_id)
    def test_too_long_is_rejected(self):
        with self.assertRaises(ValueError):
            encode_row(TinyTokenizer(),build()["train"][0],5)
    def test_loss_finite(self):
        model=LanguageModel(vocab_size=128,d_model=16,num_layers=1,hidden_dim=32,num_heads=2,context_length=512)
        row=encode_row(TinyTokenizer(),build()["train"][0],512)
        score=loss_rows(model,[row],torch.device("cpu"))
        self.assertTrue(torch.isfinite(score).item())
    def test_replay_format(self):
        self.assertGreater(len(REPLAY),0)
        self.assertTrue(all("目的:" not in r["prompt"] for r in REPLAY))
if __name__=="__main__":unittest.main()

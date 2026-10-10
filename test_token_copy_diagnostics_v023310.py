import unittest
from unittest.mock import Mock
import torch
import token_copy_diagnostics_v023310 as m
class FakeTok:
    eos_id=999
    def encode(self,text,add_bos=False,add_eos=False):
        return ([998] if add_bos else [])+[ord(c) for c in text]+([999] if add_eos else [])
    def decode(self,ids):
        return "".join(chr(i) for i in ids if i not in (998,999))
class FakeModel:
    context_length=4096
class TokenCopyTests(unittest.TestCase):
    def test_prompt_alignment(self):
        a=m.inspect_alignment(FakeTok(),"赤い本。",4096)
        self.assertTrue(a["target_alignment_ok"])
        self.assertTrue(a["answer_roundtrip"])
        self.assertTrue(a["prompt_roundtrip"])
    def test_alignment_detects_decoder_loss(self):
        class BadTok(FakeTok):
            def decode(self,ids):return super().decode(ids).replace("本","箱")
        a=m.inspect_alignment(BadTok(),"赤い本。",4096)
        self.assertFalse(a["answer_roundtrip"])
    def test_sampling_penalty_comparison(self):
        tok=FakeTok()
        fake=Mock()
        fake.tokenizer=tok
        fake.model.generate.side_effect=lambda ids,**kwargs: ids+[ord("あ"),999]
        out=m.decode_variants(fake,"あ",10)
        self.assertTrue(out["penalty_1"]["exact_copy"])
        self.assertTrue(out["penalty_1_05"]["exact_copy"])
        self.assertEqual(fake.model.generate.call_count,2)
        self.assertEqual(fake.model.generate.call_args_list[0].kwargs["repetition_penalty"],1.0)
        self.assertEqual(fake.model.generate.call_args_list[1].kwargs["repetition_penalty"],1.05)
    def test_no_checkpoint_training(self):
        self.assertTrue(callable(m.diagnose))
if __name__=="__main__":unittest.main()

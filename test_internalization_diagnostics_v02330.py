import json,tempfile,unittest
from pathlib import Path
from unittest.mock import Mock
import torch
from model import LanguageModel
from diagnose_internalization_v02330 import cases,token_metrics,prefix_probe

class ToyTokenizer:
    eos_id=2
    def encode(self,text,add_bos=False,add_eos=False):
        vals=[(ord(c)%45)+3 for c in text]
        return ([1] if add_bos else [])+vals+([2] if add_eos else [])
    def decode(self,ids,skip_special_tokens=True):
        return "".join("x" for v in ids if v not in (1,2))

class DiagnosticsTests(unittest.TestCase):
    def setUp(self):
        self.gen=Mock()
        self.gen.tokenizer=ToyTokenizer()
        self.gen.device=torch.device("cpu")
        self.gen.model=LanguageModel(vocab_size=64,d_model=16,num_layers=1,hidden_dim=32,num_heads=2,context_length=512)
        self.gen.generate.return_value={"text":"continued","generated_tokens":2,"elapsed_seconds":0.1}
    def test_teacher_metrics(self):
        m=token_metrics(self.gen,"話題: LLM\nAI: ","答え")
        self.assertGreater(m["target_tokens"],1)
        self.assertGreaterEqual(m["first_token_rank"],1)
        self.assertLessEqual(m["first_token_rank"],64)
        self.assertGreater(m["first_token_probability"],0)
        self.assertGreaterEqual(m["teacher_nll"],0)
    def test_prefix_probe(self):
        r=prefix_probe(self.gen,"AI: ","長い説明文です",0.25,24)
        self.assertGreater(r["prefix_tokens"],0)
        self.gen.generate.assert_called_once()
        self.assertEqual(self.gen.generate.call_args.kwargs["temperature"],0.0)
    def test_context_too_small(self):
        self.gen.model.context_length=2
        with self.assertRaises(ValueError):token_metrics(self.gen,"long prompt","answer")
    def test_original_cases_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"expanded.jsonl"
            rows=[
                {"id":"a:original","review_status":"APPROVED","variant_type":"original","prompt":"人: A\nAI: ","answer":"B"},
                {"id":"a:variant:0","review_status":"APPROVED","variant_type":"paraphrase","prompt":"人: A2\nAI: ","answer":"B"}
            ]
            p.write_text("".join(json.dumps(x,ensure_ascii=False)+"\n" for x in rows),encoding="utf-8")
            result=cases(p)
            self.assertEqual(len(result),1)
            self.assertEqual(result[0]["id"],"a:original")
if __name__=="__main__":unittest.main()

"""Deterministic structure-only tests; no GPU or network required."""
import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from compare_offline_four_models_v0135812 import compare

class MockTokenizer:
    vocab_size=8000;eos_id=2
    def encode(self,s,add_bos=True):return [1,3,4]
    def decode(self,ids,skip_special_tokens=True):return "長門有希。" if ids else ""
class MockModel:
    vocab_size=8000
    def eval(self):return self
    def generate(self,prefix,**kw):return prefix+[5,6]
class Tests(unittest.TestCase):
    def test_4_models_and_7_probes(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp);inputs={k:p/(k+".pt") for k in ("base","A","B","C")}
            for file in inputs.values():file.write_bytes(b"model")
            tok=p/"tok.json";tok.write_text("{}")
            with patch("tokenizer_bpe.Tokenizer.load",return_value=MockTokenizer()),\
                 patch("model.LanguageModel.load_checkpoint",return_value=(MockModel(),{})):
                r=compare(inputs,tok,p/"output.json")
            self.assertEqual(r["models"],["base","A","B","C"])
            self.assertEqual(len(r["cases"]),7)
            self.assertTrue(all(len(c["outputs"])==4 for c in r["cases"]))
            self.assertFalse(r["production_promotion_allowed"])
    def test_refuses_existing_report(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);out=p/"out.json";out.write_text("{}")
            with self.assertRaises(FileExistsError):compare({},p/"tok.json",out)
    def test_refuses_overlapping_input(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);a=p/"a";b=p/"b";a.write_bytes(b"");b.write_bytes(b"")
            with self.assertRaises(ValueError):compare({"base":a,"A":a},b,p/"out")
    def test_never_auto_selects_winner(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp);inputs={k:p/(k+".pt") for k in ("base","A","B","C")}
            for file in inputs.values():file.write_bytes(b"model")
            tok=p/"tok";tok.write_bytes(b"tok")
            with patch("tokenizer_bpe.Tokenizer.load",return_value=MockTokenizer()),\
                 patch("model.LanguageModel.load_checkpoint",return_value=(MockModel(),{})):
                r=compare(inputs,tok,p/"output.json",prompts=[{"id":"persona","category":"persona","prompt":"あなたは誰？"}])
            self.assertIsNone(r["automatic_winner"])
            self.assertFalse(r["independent_holdout_verified"])
if __name__=="__main__":unittest.main()

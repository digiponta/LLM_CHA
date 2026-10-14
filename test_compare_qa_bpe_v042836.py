import json,tempfile,unittest
from pathlib import Path
from compare_qa_bpe_v042836 import bpe_encoder,load_bpe

class FakeTokenizer:
    def encode(self,text,add_special_tokens=False):
        class Enc:pass
        r=Enc();r.ids=[ord(c)%100 for c in text];return r

class Tests(unittest.TestCase):
    def test_pair_boundaries(self):
        ids,seg=bpe_encoder(FakeTokenizer())("あ","GPU")
        self.assertEqual(ids[0],1)
        self.assertEqual(ids.count(2),1)
        self.assertEqual(len(ids),len(seg))
    def test_length(self):
        ids,seg=bpe_encoder(FakeTokenizer())("あ"*500,"い"*500)
        self.assertLessEqual(len(ids),160)
    def test_deterministic(self):
        enc=bpe_encoder(FakeTokenizer())
        self.assertEqual(enc("量子","GPU"),enc("量子","GPU"))
    def test_reject_non_bpe_format(self):
        try:import tokenizers
        except ImportError:self.skipTest("optional tokenizers library absent")
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"tokenizer.json";path.write_text(json.dumps({"model":{"type":"WordPiece"}}))
            with self.assertRaises(ValueError):load_bpe(path)
    def test_hf_bpe_file_smoke(self):
        try:from tokenizers import Tokenizer,models,pre_tokenizers,trainers
        except ImportError:self.skipTest("optional tokenizers library absent")
        tok=Tokenizer(models.BPE(unk_token="[UNK]"))
        tok.pre_tokenizer=pre_tokenizers.ByteLevel()
        tok.train_from_iterator(["GPUとは何ですか","GPUは並列処理です"],trainers.BpeTrainer(vocab_size=100,special_tokens=["[UNK]"]))
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"tok.json";tok.save(str(path))
            loaded,size=load_bpe(path)
            self.assertGreater(size,3)
            self.assertEqual(len(bpe_encoder(loaded)("GPU","並列")[0]),len(bpe_encoder(loaded)("GPU","並列")[1]))
if __name__=="__main__":unittest.main()

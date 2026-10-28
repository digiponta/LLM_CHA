import hashlib,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from prepare_jawiki_dataset_v0135821 import prepare
class T:
 @staticmethod
 def load(_):return T()
 def encode(self,text,add_bos=False,add_eos=False):
  return ([1] if add_bos else [])+[10+ord(c)%40 for c in text]+([2] if add_eos else [])
class Tests(unittest.TestCase):
 def data(self,root):
  source=root/"source.jsonl";quality=root/"quality.json";tokenizer=root/"tok.json"
  rows=[{"article_id":str(i),"title":"項目"+str(i),"source_url":"https://ja.wikipedia.org/?curid="+str(i),
         "paragraph_index":0,"text":"日本語の学習データです。"*20,"approval":"PENDING_REVIEW","auto_promote":False}
        for i in range(1,11)]
  source.write_text("".join(json.dumps(x,ensure_ascii=False)+"\n" for x in rows),encoding="utf8")
  quality.write_text(json.dumps({"sha256":{"clean_candidates.jsonl":hashlib.sha256(source.read_bytes()).hexdigest()}}),encoding="utf8")
  tokenizer.write_text("{}",encoding="utf8")
  return source,quality,tokenizer
 @patch("tokenizer_bpe.Tokenizer",T)
 def test_disjoint_and_bounded(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);a,b,c=self.data(root);out=root/"output"
   r=prepare(a,b,c,out,max_tokens=32)
   self.assertTrue(r["article_split_disjoint"])
   self.assertFalse(r["independent_holdout_verified"])
   train=[json.loads(x) for x in (out/"train_chunks.jsonl").read_text().splitlines()]
   val=[json.loads(x) for x in (out/"validation_chunks.jsonl").read_text().splitlines()]
   self.assertFalse({x["article_id"] for x in train}&{x["article_id"] for x in val})
   self.assertTrue(all(len(x["token_ids"])<=33 and x["supervised_tokens"]<=32 for x in train+val))
 @patch("tokenizer_bpe.Tokenizer",T)
 def test_no_overwrite(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);a,b,c=self.data(root);out=root/"out";prepare(a,b,c,out)
   with self.assertRaises(FileExistsError):prepare(a,b,c,out)
 def test_source_integrity(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);a,b,c=self.data(root);a.write_text("tampered",encoding="utf8")
   with self.assertRaises(ValueError):prepare(a,b,c,root/"out")
 @patch("tokenizer_bpe.Tokenizer",T)
 def test_invalid_context(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);a,b,c=self.data(root)
   with self.assertRaises(ValueError):prepare(a,b,c,root/"out",max_tokens=513)
if __name__=="__main__":unittest.main()

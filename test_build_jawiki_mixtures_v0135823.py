import hashlib,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from build_jawiki_mixtures_v0135823 import build,dialogue_chunks

class Tok:
 @staticmethod
 def load(_):return Tok()
 def encode(self,s,add_bos=False,add_eos=False):
  return ([1] if add_bos else [])+[10+(ord(c)%100) for c in s]+([2] if add_eos else [])

class Tests(unittest.TestCase):
 def fixtures(self,root):
  d=root/"dataset";d.mkdir();tok=root/"tok.json";tok.write_text("{}",encoding="utf-8")
  sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
  paths={}
  for label,article in (("train","101"),("validation","202")):
   p=d/(label+"_chunks.jsonl")
   data=[{"article_id":article,"title":"日本語","url":"https://ja.wikipedia.org/?curid="+article,
          "approval":"PENDING_REVIEW","auto_promote":False,
          "token_ids":list(range(1,52)),"supervised_tokens":50} for _ in range(40)]
   p.write_text("".join(json.dumps(x,ensure_ascii=False)+"\n" for x in data),encoding="utf-8")
   paths[p.name]=sha(p)
  (d/"manifest.json").write_text(json.dumps({"status":"STAGED_NOT_APPROVED",
      "max_context_tokens":512,"tokenizer_sha256":sha(tok),"file_sha256":paths}),encoding="utf-8")
  sources=[]
  for domain in ("conversation","persona"):
   p=root/(domain+".jsonl")
   p.write_text("".join(json.dumps({"approved":True,"user":"日本語について教えて","assistant":"文章について説明します。"},ensure_ascii=False)+"\n" for _ in range(4)),encoding="utf-8")
   sources.append(p)
  return d,tok,*sources
 def test_masked_replay(self):
  examples=list(dialogue_chunks("人: こんにちは\nAI: そう。",Tok(),512,"persona",0))
  self.assertEqual(len(examples),1)
  self.assertLess(sum(examples[0]["loss_mask"]),len(examples[0]["loss_mask"]))
  self.assertGreater(examples[0]["supervised_tokens"],0)
 @patch("tokenizer_bpe.Tokenizer",Tok)
 def test_disjoint_and_unapproved(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);d,t,c,p=self.fixtures(root)
   r=build(d,t,c,p,root/"output",budget=300,max_reuse=3)
   self.assertFalse(r["training_performed"])
   self.assertFalse(r["validation_used_for_training"])
   self.assertEqual(set(r["experiments"]),{"W","WR","WRP"})
   self.assertEqual(r["experiments"]["W"]["actual_supervised_tokens"].get("wiki"),300)
   rows=[json.loads(s) for s in (root/"output"/"WRP_mixture.jsonl").read_text(encoding="utf-8").splitlines()]
   self.assertTrue(all(row["article_id"]=="101" for row in rows if row["domain"]=="wiki"))
   self.assertTrue(all(len(row["loss_mask"])==len(row["token_ids"])-1 for row in rows))
 @patch("tokenizer_bpe.Tokenizer",Tok)
 def test_no_overwrite(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);d,t,c,p=self.fixtures(root);out=root/"output"
   build(d,t,c,p,out,budget=300)
   with self.assertRaises(FileExistsError):build(d,t,c,p,out,budget=300)
 @patch("tokenizer_bpe.Tokenizer",Tok)
 def test_tampered_wiki_refused(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);d,t,c,p=self.fixtures(root)
   (d/"train_chunks.jsonl").write_text("tampered",encoding="utf-8")
   with self.assertRaises(ValueError):build(d,t,c,p,root/"out")
if __name__=="__main__":unittest.main()

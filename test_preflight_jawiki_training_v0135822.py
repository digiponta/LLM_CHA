import hashlib,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from preflight_jawiki_training_v0135822 import inspect

class Tests(unittest.TestCase):
 def fixtures(self,p):
  folder=p/"dataset";folder.mkdir()
  tok=p/"tok.json";tok.write_text("{}",encoding="utf-8")
  cp=p/"model.pt";cp.write_bytes(b"mock")
  files={};totals={}
  for name,id in [("train","42"),("validation","43")]:
   r={"article_id":id,"title":"記事","url":"https://ja.wikipedia.org/?curid="+id,
      "token_ids":[1,2,3],"supervised_tokens":2,
      "approval":"PENDING_REVIEW","auto_promote":False}
   f=folder/(name+"_chunks.jsonl")
   f.write_text(json.dumps(r,ensure_ascii=False)+"\n",encoding="utf-8")
   files[f.name]=hashlib.sha256(f.read_bytes()).hexdigest()
   totals[name]=1
  (folder/"manifest.json").write_text(json.dumps({
    "status":"STAGED_NOT_APPROVED","max_context_tokens":512,
    "tokenizer_sha256":hashlib.sha256(tok.read_bytes()).hexdigest(),
    "file_sha256":files,"chunks":totals,
    "supervised_tokens":{"train":2,"validation":2},
    "articles":{"train":1,"validation":1}
  }),encoding="utf-8")
  return folder,tok,cp
 @patch("torch.load",return_value={"config":{"vocab_size":8000,"context_length":512}})
 def test_valid_but_blocked(self,_):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);folder,tok,cp=self.fixtures(p)
   r=inspect(folder,tok,cp,p/"report.json")
   self.assertTrue(r["article_disjoint"])
   self.assertEqual(r["issues"],["PLAN_SOURCE_MISSING_WRP_conversation","PLAN_SOURCE_MISSING_WRP_persona","PLAN_SOURCE_MISSING_WR_conversation"])
   self.assertEqual(r["status"],"PREFLIGHT_BLOCKED")
   self.assertFalse(r["training_performed"])
 @patch("torch.load",return_value={"config":{"vocab_size":8000,"context_length":512}})
 def test_detect_tamper(self,_):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);folder,tok,cp=self.fixtures(p)
   (folder/"train_chunks.jsonl").write_text('{"bad":true}\n',encoding="utf-8")
   r=inspect(folder,tok,cp,p/"report.json")
   self.assertIn("DATASET_HASH_MISMATCH_TRAIN",r["issues"])
 @patch("torch.load",return_value={"config":{"vocab_size":8000,"context_length":512}})
 def test_no_overwrite(self,_):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);folder,tok,cp=self.fixtures(p);output=p/"report.json"
   inspect(folder,tok,cp,output)
   with self.assertRaises(FileExistsError):inspect(folder,tok,cp,output)
if __name__=="__main__":unittest.main()

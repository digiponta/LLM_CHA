import hashlib,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from evaluate_jawiki_shared_v0135826 import verify,evaluate,compute_nll

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
class Tests(unittest.TestCase):
 def fixtures(self,root):
  dataset=root/"dataset";dataset.mkdir();trained=root/"trained";trained.mkdir()
  tok=root/"tok.json";tok.write_text("{}",encoding="utf-8")
  base=root/"base.pt";base.write_bytes(b"base")
  paths={}
  for a in ("W","WR","WRP"):
   p=trained/("candidate_"+a+".pt");p.write_bytes(a.encode());paths[a]=p
  hashes={}
  for split,article in (("train","10"),("validation","20")):
   p=dataset/(split+"_chunks.jsonl")
   p.write_text(json.dumps({"article_id":article,"token_ids":[1,2,3],
      "supervised_tokens":2,"approval":"PENDING_REVIEW","auto_promote":False})+"\n",encoding="utf-8")
   hashes[p.name]=sha(p)
  (dataset/"manifest.json").write_text(json.dumps({
      "status":"STAGED_NOT_APPROVED","validation_scope":"SAME_DUMP_DIAGNOSTIC_ONLY",
      "tokenizer_sha256":sha(tok),"file_sha256":hashes,"chunks":{"validation":1},
      "supervised_tokens":{"validation":2}}),encoding="utf-8")
  (trained/"report.json").write_text(json.dumps({"status":"EXPLORATORY_TRAINING_COMPLETE",
       "checkpoint_sha256":sha(base),"tokenizer_sha256":sha(tok),
       "history":{a:{"checkpoint_sha256":sha(p)} for a,p in paths.items()}}),encoding="utf-8")
  return dataset,trained,base,tok
 def test_preflight_no_output(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);paths=self.fixtures(root);output=root/"report.json"
   result=evaluate(*paths,output,dry_run=True)
   self.assertEqual(result["validation_supervised_tokens"],2)
   self.assertFalse(output.exists())
 def test_validation_tamper_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);paths=self.fixtures(root)
   (paths[0]/"validation_chunks.jsonl").write_text("bad",encoding="utf-8")
   with self.assertRaises(ValueError):verify(*paths,root/"result.json")
 def test_candidate_tamper_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);paths=self.fixtures(root)
   (paths[1]/"candidate_WR.pt").write_bytes(b"bad")
   with self.assertRaises(ValueError):verify(*paths,root/"result.json")
 def test_output_overwrite_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);paths=self.fixtures(root);out=root/"result.json";out.write_text("{}")
   with self.assertRaises(FileExistsError):verify(*paths,out)
if __name__=="__main__":unittest.main()

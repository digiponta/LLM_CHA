import hashlib,json,tempfile,unittest
from pathlib import Path
from train_corrective_sft_v0135830 import preflight

class Tests(unittest.TestCase):
 def fixture(self,root):
  source=root/"reviewed.jsonl";rows=[]
  for i in range(8):
   rows.append({"id":f"id-{i}","user":f"質問{i}","assistant":f"回答{i}。",
    "approved":True,"reviewer":"ChatGPT GPT-6","approval_scope":"candidate_corrective_sft_only",
    "training_authorized":False,"production_promotion_allowed":False})
  source.write_text("".join(json.dumps(r,ensure_ascii=False)+"\n" for r in rows),encoding="utf-8")
  audit=root/"audit.json";audit.write_text(json.dumps({
   "version":"v0.13.58.29","status":"ASSISTANT_CONTENT_REVIEW_RECORDED",
   "approved_for_candidate_dataset":True,"source_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),
   "training_performed":False,"human_reviewer_attested":False}),encoding="utf-8")
  base=root/"base.pt";base.write_bytes(b"base")
  tok=root/"tok.json";tok.write_bytes(b"tok")
  return source,audit,base,tok
 def test_preflight_only(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);args=self.fixture(root);output=root/"out"
   lines,r=preflight(*args,output,40,4,3e-6)
   self.assertEqual(len(lines),8)
   self.assertFalse(r["training_performed"])
   self.assertFalse(output.exists())
 def test_sha_tamper(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);args=self.fixture(root)
   args[0].write_text(args[0].read_text(encoding="utf-8")+"{}",encoding="utf-8")
   with self.assertRaises(ValueError):preflight(*args,root/"out",40,4,3e-6)
 def test_no_overwrite(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);args=self.fixture(root);output=root/"out";output.mkdir()
   with self.assertRaises(FileExistsError):preflight(*args,output,40,4,3e-6)
 def test_parameters(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);args=self.fixture(root)
   with self.assertRaises(ValueError):preflight(*args,root/"out",0,4,3e-6)
if __name__=="__main__":unittest.main()

import hashlib,json,tempfile,unittest
from pathlib import Path
from evaluate_corrective_effect_v0135831 import preflight,PARAPHRASES

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
class Tests(unittest.TestCase):
 def fixture(self,root):
  base=root/"base.pt";base.write_bytes(b"base")
  candidate=root/"candidate.pt";candidate.write_bytes(b"candidate")
  tok=root/"tok.json";tok.write_bytes(b"tokenizer")
  reviewed=root/"reviewed.jsonl"
  records=[{"id":f"item-{i}","user":f"質問{i}","assistant":f"回答{i}","domain":"conversation","approved":True} for i in range(8)]
  reviewed.write_text("".join(json.dumps(x,ensure_ascii=False)+"\n" for x in records),encoding="utf-8")
  report=root/"report.json";report.write_text(json.dumps({"version":"v0.13.58.30",
   "status":"EXPLORATORY_CORRECTIVE_TRAINING_COMPLETE","base_sha256":sha(base),
   "checkpoint_sha256":sha(candidate),"tokenizer_sha256":sha(tok),"source_sha256":sha(reviewed)}),encoding="utf-8")
  return report,base,candidate,tok,reviewed
 def test_preflight(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);args=self.fixture(root)
   probes,_=preflight(*args,root/"output.json",64)
   self.assertEqual(len(probes),14)
   self.assertEqual(sum(p["set"]=="exposed_train" for p in probes),8)
   self.assertEqual(len(PARAPHRASES),6)
 def test_checkpoint_tamper(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);args=self.fixture(root);args[2].write_bytes(b"tamper")
   with self.assertRaises(ValueError):preflight(*args,root/"out.json",64)
 def test_no_overwrite(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);args=self.fixture(root);out=root/"out.json";out.write_text("{}")
   with self.assertRaises(FileExistsError):preflight(*args,out,64)
 def test_invalid_budget(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);args=self.fixture(root)
   with self.assertRaises(ValueError):preflight(*args,root/"out.json",0)
if __name__=="__main__":unittest.main()

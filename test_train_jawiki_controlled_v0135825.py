import hashlib,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from train_jawiki_controlled_v0135825 import verify,run

TOKEN_HASH="4f9c7266c88468d0b0b7789ae2bdba03cbe7103d546b2a64eb57dd34e37fb3fc"
class FakeModel:
 context_length=512
 vocab_size=8000
class FakeLM:
 @staticmethod
 def load_checkpoint(path,device=None):return FakeModel(),{}
class Tests(unittest.TestCase):
 def fixtures(self,root):
  d=root/"data";d.mkdir();hashes={}
  for arm in ("W","WR","WRP"):
   p=d/(arm+"_balanced.jsonl")
   p.write_text(json.dumps({"domain":"wiki","token_ids":[1,2,3],
       "loss_mask":[1,1],"supervised_tokens":2,
       "approval":"EXPERIMENT_CANDIDATE_ONLY"})+"\n",encoding="utf-8")
   hashes[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
  (d/"manifest.json").write_text(json.dumps({"status":"BALANCED_STAGED_NOT_APPROVED","file_sha256":hashes}),encoding="utf-8")
  tok=root/"tok.json";tok.write_text("{}",encoding="utf-8")
  model=root/"model.pt";model.write_bytes(b"fake")
  return d,tok,model
 def checked(self,d,t,m,out):
  original=__import__("train_jawiki_controlled_v0135825").sha
  with patch("model.LanguageModel",FakeLM),patch("train_jawiki_controlled_v0135825.sha",side_effect=lambda p:TOKEN_HASH if p==t else original(p)):
   return verify(d,t,m,out,["W","WR","WRP"],20,4,3e-6,123)
 def test_dry_run_is_not_training(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);d,t,m=self.fixtures(root);out=root/"out"
   report,rows=self.checked(d,t,m,out)
   self.assertEqual(report["status"],"DRY_RUN_ONLY")
   self.assertFalse(report["training_performed"])
   self.assertFalse(out.exists())
   self.assertEqual(len(rows["WRP"]),1)
 def test_tamper_rejected(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);d,t,m=self.fixtures(root)
   (d/"WR_balanced.jsonl").write_text("tampered",encoding="utf-8")
   with self.assertRaises(ValueError):self.checked(d,t,m,root/"out")
 def test_existing_output_rejected(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);d,t,m=self.fixtures(root);out=root/"out";out.mkdir()
   with self.assertRaises(FileExistsError):self.checked(d,t,m,out)
 def test_wrong_hyperparameters_rejected(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);d,t,m=self.fixtures(root)
   with self.assertRaises(ValueError):
    verify(d,t,m,root/"out",["W"],0,4,3e-6,123)
if __name__=="__main__":unittest.main()

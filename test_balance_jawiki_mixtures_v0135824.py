import hashlib,json,tempfile,unittest
from pathlib import Path
from balance_jawiki_mixtures_v0135824 import balance

class Tests(unittest.TestCase):
 def fixture(self,root):
  folder=root/"input";folder.mkdir()
  hashes={};exps={}
  for arm,wiki,replay in (("W",30,0),("WR",25,3),("WRP",20,5)):
   rows=[{"domain":"wiki","token_ids":list(range(102)),"loss_mask":[1]*101,
          "supervised_tokens":101,"repeat_index":0,"approval":"EXPERIMENT_CANDIDATE_ONLY"} for _ in range(wiki)]
   rows += [{"domain":"conversation","token_ids":[1,2,3,4],"loss_mask":[0,1,1],
             "supervised_tokens":2,"repeat_index":i%3,"approval":"EXPERIMENT_CANDIDATE_ONLY"} for i in range(replay)]
   path=folder/(arm+"_mixture.jsonl")
   path.write_text("".join(json.dumps(r)+"\n" for r in rows),encoding="utf-8")
   hashes[path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
   exps[arm]={"target_weights":{"wiki":1.0}}
  (folder/"manifest.json").write_text(json.dumps({
     "status":"EXPERIMENT_DATA_STAGED_NOT_APPROVED",
     "output_sha256":hashes,"experiments":exps}),encoding="utf-8")
  return folder
 def test_balancing(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);folder=self.fixture(root)
   report=balance(folder,root/"output",tolerance=110)
   self.assertFalse(report["training_performed"])
   for info in report["experiments"].values():
    self.assertLessEqual(abs(info["deviation_tokens"]),110)
    self.assertLessEqual(info["max_reuse_observed"],3)
 def test_integrity_rejects_modification(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);folder=self.fixture(root)
   (folder/"W_mixture.jsonl").write_text("tampered",encoding="utf-8")
   with self.assertRaises(ValueError):balance(folder,root/"output")
 def test_never_overwrite(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);folder=self.fixture(root)
   balance(folder,root/"output",tolerance=110)
   with self.assertRaises(FileExistsError):balance(folder,root/"output",tolerance=110)
if __name__=="__main__":unittest.main()

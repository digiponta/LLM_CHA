import hashlib,json,tempfile,unittest
from pathlib import Path
from evaluate_jawiki_generation_v0135827 import check,PROBES
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
class Tests(unittest.TestCase):
 def fixture(self,root):
  trained=root/"trained";trained.mkdir()
  base=root/"base.pt";base.write_bytes(b"original")
  tok=root/"tokenizer.json";tok.write_text("{}",encoding="utf-8")
  history={}
  for arm in ("W","WR","WRP"):
   path=trained/("candidate_"+arm+".pt");path.write_bytes(arm.encode())
   history[arm]={"checkpoint_sha256":sha(path)}
  (trained/"report.json").write_text(json.dumps({"status":"EXPLORATORY_TRAINING_COMPLETE",
     "checkpoint_sha256":sha(base),"tokenizer_sha256":sha(tok),"history":history}),encoding="utf-8")
  return trained,base,tok
 def test_provenance(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);args=self.fixture(root)
   p=check(*args,root/"out.json",64)
   self.assertEqual(set(p),{"Base","W","WR","WRP"})
 def test_tamper(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);args=self.fixture(root)
   (args[0]/"candidate_WR.pt").write_bytes(b"tampered")
   with self.assertRaises(ValueError):check(*args,root/"out.json",64)
 def test_no_overwrite(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);args=self.fixture(root);out=root/"out.json";out.write_text("{}")
   with self.assertRaises(FileExistsError):check(*args,out,64)
 def test_probes_and_limits(self):
  self.assertEqual(len(PROBES),8)
  self.assertEqual(len(set(p["id"] for p in PROBES)),8)
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);args=self.fixture(root)
   with self.assertRaises(ValueError):check(*args,root/"out.json",0)
if __name__=="__main__":unittest.main()

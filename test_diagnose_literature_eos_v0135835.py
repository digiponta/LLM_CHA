import json,tempfile,unittest
from pathlib import Path
from diagnose_literature_eos_v0135835 import PROBES,verify,STAGE_SHA
class Tests(unittest.TestCase):
 def test_probe_ids(self):
  self.assertEqual(len(PROBES),5)
  self.assertEqual(len({p["id"] for p in PROBES}),5)
 def test_provenance_constant(self):
  self.assertEqual(len(STAGE_SHA),64)
 def test_no_overwrite(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);out=root/"out.json";out.write_text("{}")
   with self.assertRaises(FileExistsError):
    verify(root/"start.pt",root/"report.json",root/"stages.jsonl",root/"tok.json",out)
 def test_invalid_report(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);report=root/"report.json";report.write_text(json.dumps({"version":"v0.13.58.33","status":"STOPPED_ITEM_LIMIT"}))
   with self.assertRaises(ValueError):
    verify(root/"start.pt",report,root/"stages.jsonl",root/"tok.json",root/"out.json")
if __name__=="__main__":unittest.main()

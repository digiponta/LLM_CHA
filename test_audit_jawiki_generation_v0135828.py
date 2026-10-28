import json,tempfile,unittest
from pathlib import Path
from audit_jawiki_generation_v0135828 import audit,audit_item,EXPECTED
class Tests(unittest.TestCase):
 def test_missing_concept(self):
  r=audit_item({"id":"cpu","raw_answer":"予測と関連する方法。","eos_reached":True})
  self.assertIn("MISSING_EXPECTED_CONCEPT",r["flags"])
 def test_repetition_and_eos(self):
  r=audit_item({"id":"tired","raw_answer":"休日を休日を休日を休日を","eos_reached":False})
  self.assertIn("REPETITION_PATTERN",r["flags"])
  self.assertIn("NO_EOS_WITHIN_BUDGET",r["flags"])
 def test_identity(self):
  r=audit_item({"id":"identity","raw_answer":"長門有希。","eos_reached":True})
  self.assertEqual(r["flags"],[])
 def test_full_report_and_no_overwrite(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);source=root/"source.json";out=root/"out.json"
   probes=[{"id":key,"user":key} for key in EXPECTED]
   results={name:[{"id":p["id"],"user":p["user"],"raw_answer":"長門有希。","eos_reached":True} for p in probes] for name in ("Base","W","WR","WRP")}
   source.write_text(json.dumps({"version":"v0.13.58.27","status":"RAW_GENERATION_DIAGNOSTIC","probes":probes,"results":results}),encoding="utf-8")
   r=audit(source,out)
   self.assertEqual(r["status"],"HEURISTIC_AUDIT_COMPLETE")
   self.assertFalse(r["semantic_consistency_verified"])
   with self.assertRaises(FileExistsError):audit(source,out)
if __name__=="__main__":unittest.main()

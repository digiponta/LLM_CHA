import json,tempfile,unittest
from pathlib import Path
from propose_rse_unified_repair_v013588317 import propose
from apply_rse_unified_repair_v013588318 import repair
class SafeRepairTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
  d=Path(self.temp.name)
  self.a=d/"atomic.jsonl";self.u=d/"unified.jsonl";self.p=d/"proposal.json"
  self.a.write_text(json.dumps({"subject":"閃亜鉛鉱","value":"亜鉛の硫化鉱物である"},ensure_ascii=False)+"\n",encoding="utf-8")
  self.u.write_text("".join(json.dumps(x,ensure_ascii=False)+"\n" for x in [
    {"concept":"GPU","assistant":"GPUは処理装置","metadata":7},
    {"concept":"閃亜鉛鉱","assistant":"閃亜鉛鉱は、亜鉛の硫化鉱物であるである。","source":"atomic-proposition"}]),encoding="utf-8")
  self.p.write_text(json.dumps(propose(self.a,self.u),ensure_ascii=False),encoding="utf-8")
 def test_default_dry_run(self):
  before=self.u.read_bytes();x=repair(self.a,self.u,self.p)
  self.assertFalse(x["applied"]);self.assertEqual(self.u.read_bytes(),before)
 def test_apply_with_backup(self):
  before=self.u.read_bytes()
  x=repair(self.a,self.u,self.p,True,"閃亜鉛鉱")
  self.assertEqual(x["status"],"APPLIED_VERIFIED")
  self.assertEqual(Path(x["backup"]).read_bytes(),before)
  rows=[json.loads(t) for t in self.u.read_text(encoding="utf-8").splitlines()]
  self.assertEqual(rows[0]["metadata"],7)
  self.assertEqual(rows[1]["assistant"],"閃亜鉛鉱は、亜鉛の硫化鉱物である。")
 def test_requires_explicit_approval(self):
  with self.assertRaises(ValueError):repair(self.a,self.u,self.p,True)
 def test_stale_proposal_blocked(self):
  self.u.write_text(self.u.read_text(encoding="utf-8")+"\n",encoding="utf-8")
  # semantic equality alone does not guard byte changes: only changes to case structure are blocked.
  rows=[json.loads(t) for t in self.u.read_text(encoding="utf-8").splitlines() if t.strip()]
  rows[1]["assistant"]="別の回答"
  self.u.write_text("".join(json.dumps(x,ensure_ascii=False)+"\n" for x in rows),encoding="utf-8")
  with self.assertRaises(ValueError):repair(self.a,self.u,self.p)
if __name__=="__main__":unittest.main()

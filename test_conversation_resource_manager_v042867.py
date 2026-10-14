import json
import tempfile
import unittest
from pathlib import Path
from conversation_resource_memory_v042866 import new_conversation,append_turn,close_session,sleep_checkpoint,write_json_atomic
from conversation_resource_manager_v042867 import plan,apply_plan

class ResourceManagerTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory()
  self.addCleanup(self.tmp.cleanup)
  self.root=Path(self.tmp.name)/"store"
  self.root.mkdir()
  self.audit=Path(self.tmp.name)/"audit.json"
 def add(self,name,*,completed=True,active=False):
  m=new_conversation(name)
  append_turn(m,"A","合成会話です")
  close_session(m)
  if completed:sleep_checkpoint(m,1,completed=True)
  if active:m["active"]=True
  path=self.root/(name+".conversation.json")
  write_json_atomic(m,path)
  return path
 def test_dry_run_preserves(self):
  p=self.add("a")
  r=plan(self.root,0)
  self.assertEqual(len(r["candidate_files"]),1)
  self.assertTrue(p.exists())
 def test_apply(self):
  p=self.add("a")
  r=plan(self.root,0)
  result=apply_plan(r,self.audit)
  self.assertFalse(p.exists())
  self.assertTrue(self.audit.exists())
  self.assertTrue(result["budget_satisfied_actual"])
 def test_pending_protected(self):
  self.add("a",completed=False)
  self.assertEqual(plan(self.root,0)["candidate_files"],[])
 def test_active_protected(self):
  self.add("a",active=True)
  self.assertEqual(plan(self.root,0)["candidate_files"],[])
 def test_unsupported_files_untouched(self):
  self.add("a")
  outside=self.root/"facts.json"
  outside.write_text("do not delete",encoding="utf-8")
  apply_plan(plan(self.root,0),self.audit)
  self.assertTrue(outside.exists())
 def test_duplicate_rejected(self):
  a=self.add("a");(self.root/"b.conversation.json").write_bytes(a.read_bytes())
  with self.assertRaises(ValueError):plan(self.root,0)
 def test_checksum_change_aborts(self):
  p=self.add("a");r=plan(self.root,0)
  p.write_bytes(p.read_bytes()+b" ")
  with self.assertRaises(ValueError):apply_plan(r,self.audit)
  self.assertTrue(p.exists())
 def test_external_audit(self):
  self.add("a")
  with self.assertRaises(ValueError):apply_plan(plan(self.root,0),self.root/"audit.json")
 def test_nonzero_budget(self):
  self.add("a")
  p=plan(self.root,10**8)
  self.assertEqual(p["candidate_files"],[])
 def test_bad_budget(self):
  with self.assertRaises(ValueError):plan(self.root,-1)
if __name__=="__main__":unittest.main()

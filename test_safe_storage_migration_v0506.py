import json
import tempfile
import unittest
from pathlib import Path
from benchmark_long_conversation_resources_v042871 import make_session
from conversation_resource_memory_v042866 import write_json_atomic
from safe_storage_migration_v0506 import migrate

class SafeMigrationTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory()
  self.addCleanup(self.temp.cleanup)
  root=Path(self.temp.name)
  source_dir=root/"conversation";dest_dir=root/"artifacts"
  source_dir.mkdir();dest_dir.mkdir()
  self.source=source_dir/"sample.conversation.json"
  self.compact=dest_dir/"compact.json"
  self.receipt=dest_dir/"receipt.json"
  write_json_atomic(make_session(20),self.source)
 def call(self,**kw):
  return migrate(self.source,self.compact,self.receipt,**kw)
 def test_save_and_verify(self):
  result=self.call()
  self.assertTrue(self.compact.exists())
  self.assertEqual(result["turns_verified"],20)
 def test_source_retained(self):
  result=self.call()
  self.assertTrue(self.source.exists())
  self.assertFalse(result["deletion_performed"])
 def test_retry(self):
  self.call();result=self.call()
  self.assertEqual(result["artifact"],"EXISTING_VERIFIED")
  self.assertEqual(result["receipt"],"EXISTING_VERIFIED")
 def test_fault_after_artifact_recovery(self):
  with self.assertRaises(RuntimeError):self.call(inject_failure="after_artifact")
  self.assertTrue(self.source.exists())
  self.assertTrue(self.compact.exists())
  self.assertFalse(self.receipt.exists())
  self.assertEqual(self.call()["artifact"],"EXISTING_VERIFIED")
 def test_fault_after_receipt_recovery(self):
  with self.assertRaises(RuntimeError):self.call(inject_failure="after_receipt")
  self.assertTrue(self.source.exists())
  self.assertEqual(self.call()["receipt"],"EXISTING_VERIFIED")
 def test_corrupt_compact_rejected(self):
  self.call()
  payload=json.loads(self.compact.read_text(encoding="utf-8"))
  payload["texts"][0]="corrupt"
  write_json_atomic(payload,self.compact)
  with self.assertRaises(ValueError):self.call()
  self.assertTrue(self.source.exists())
 def test_corrupt_receipt_rejected(self):
  self.call()
  data=json.loads(self.receipt.read_text(encoding="utf-8"))
  data["source_turns"]=99
  write_json_atomic(data,self.receipt)
  with self.assertRaises(ValueError):self.call()
 def test_unmatched_retained(self):
  write_json_atomic(make_session(20,5),self.source)
  self.call()
  receipt=json.loads(self.receipt.read_text(encoding="utf-8"))
  self.assertEqual(receipt["uncovered_turns"],4)
 def test_active_rejected(self):
  m=make_session(20);m["active"]=True
  write_json_atomic(m,self.source)
  with self.assertRaises(ValueError):self.call()
 def test_same_paths_rejected(self):
  with self.assertRaises(ValueError):
   migrate(self.source,self.source,self.receipt)
 def test_output_inside_source_dir_rejected(self):
  with self.assertRaises(ValueError):
   migrate(self.source,self.source.parent/"compact.json",self.receipt)
 def test_receipt_safety(self):
  self.call()
  r=json.loads(self.receipt.read_text(encoding="utf-8"))
  self.assertFalse(r["approved_for_eviction"])
  self.assertEqual(r["source_turns"],r["reconstructed_turns"])
if __name__=="__main__":unittest.main()

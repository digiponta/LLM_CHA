import json
import tempfile
import unittest
from pathlib import Path
from conversation_resource_memory_v042866 import new_conversation,append_turn,close_session,write_json_atomic
from conversation_sleep_backend_v042868 import extract
from proposition_memory_lifecycle_v042869 import import_candidates,transition,run_import,validate

class PropositionLifecycleTests(unittest.TestCase):
 def setUp(self):
  m=new_conversation("synthetic-session")
  append_turn(m,"A","私は音楽が好き")
  close_session(m)
  self.source=extract(m)
  self.memory=import_candidates(self.source)
  self.pid=self.memory["items"][0]["id"]
 def test_initial(self):
  self.assertEqual(self.memory["items"][0]["state"],"CANDIDATE")
 def test_no_fact_promotion(self):
  self.assertFalse(self.memory["fact_promoted"])
  self.assertFalse(self.memory["items"][0]["fact_verified"])
 def test_review(self):
  transition(self.memory,self.pid,"review",reviewer="tester",reason="check evidence")
  self.assertEqual(self.memory["items"][0]["state"],"REVIEW_REQUIRED")
 def test_verify_requires_evidence(self):
  transition(self.memory,self.pid,"review",reviewer="tester",reason="check")
  with self.assertRaises(ValueError):transition(self.memory,self.pid,"verify",reviewer="tester",reason="yes")
 def test_verify_report_not_fact(self):
  transition(self.memory,self.pid,"review",reviewer="tester",reason="check")
  transition(self.memory,self.pid,"verify",reviewer="tester",reason="source checked",evidence_reference="local-review-001")
  self.assertTrue(self.memory["items"][0]["reviewed_report"])
  self.assertFalse(self.memory["items"][0]["fact_verified"])
 def test_reject(self):
  transition(self.memory,self.pid,"reject",reviewer="tester",reason="incorrect attribution")
  self.assertEqual(self.memory["items"][0]["state"],"REJECTED")
 def test_supersede(self):
  transition(self.memory,self.pid,"review",reviewer="tester",reason="checking")
  transition(self.memory,self.pid,"supersede",reviewer="tester",reason="correction")
  self.assertEqual(self.memory["items"][0]["state"],"SUPERSEDED")
 def test_terminal(self):
  transition(self.memory,self.pid,"reject",reviewer="tester",reason="bad")
  with self.assertRaises(ValueError):transition(self.memory,self.pid,"review",reviewer="tester",reason="again")
 def test_audit(self):
  transition(self.memory,self.pid,"review",reviewer="tester",reason="source")
  self.assertEqual(self.memory["items"][0]["review_events"][0]["reviewer"],"tester")
 def test_no_reviewer(self):
  with self.assertRaises(ValueError):transition(self.memory,self.pid,"review",reviewer="",reason="x")
 def test_rollback(self):
  before=json.dumps(self.memory,sort_keys=True)
  with self.assertRaises(ValueError):transition(self.memory,self.pid,"verify",reviewer="tester",reason="skip review",evidence_reference="ref")
  self.assertEqual(json.dumps(self.memory,sort_keys=True),before)
 def test_import_idempotent(self):
  with tempfile.TemporaryDirectory() as td:
   src=Path(td)/"candidates.json";dst=Path(td)/"review.json"
   write_json_atomic(self.source,src)
   a=run_import(src,dst)
   transition(a,a["items"][0]["id"],"review",reviewer="tester",reason="check")
   write_json_atomic(a,dst)
   b=run_import(src,dst)
   self.assertEqual(b["items"][0]["state"],"REVIEW_REQUIRED")
 def test_source_change_refused(self):
  with tempfile.TemporaryDirectory() as td:
   src=Path(td)/"candidates.json";dst=Path(td)/"review.json"
   write_json_atomic(self.source,src);run_import(src,dst)
   changed=dict(self.source);changed["source_fingerprint"]="b"*64
   write_json_atomic(changed,src)
   with self.assertRaises(ValueError):run_import(src,dst)
 def test_no_source_text_export_in_summary(self):
  self.assertTrue(validate(self.memory))
if __name__=="__main__":unittest.main()

import json
import tempfile
import unittest
from pathlib import Path
from copy import deepcopy
from benchmark_long_conversation_resources_v042871 import make_session
from benchmark_compact_evidence_v0502 import pack
from incremental_sleep_v0503 import initialize,update,commit,benchmark

class IncrementalSleepTests(unittest.TestCase):
 def partial(self,m,n):
  p=deepcopy(m);p["turns"]=deepcopy(m["turns"][:n]);p["last_turn"]=n
  p["sleep"]={"processed_turn":0,"completed":False};p["status"]="PENDING_SLEEP"
  return p
 def test_stages_equivalent(self):
  m=make_session(100)
  a=update(self.partial(m,10))
  a=update(self.partial(m,40),a)
  a=update(m,a);b=pack(m)
  for key in ("texts","turns","propositions","occurrences","uncovered_turn_ids"):
   self.assertEqual(a[key],b[key])
 def test_replay_idempotent(self):
  m=make_session(10);a=update(m)
  self.assertEqual(update(m,a),a)
 def test_uncovered(self):
  m=make_session(30,3);a=update(m)
  self.assertEqual(a["uncovered_turn_ids"],list(range(3,31,3)))
 def test_source_edit_refused(self):
  m=make_session(10);a=update(m)
  changed=deepcopy(m);changed["turns"][0]["text"]="改ざん"
  with self.assertRaises(ValueError):update(changed,a)
 def test_modified_artifact_refused(self):
  m=make_session(10);a=update(m)
  a["texts"][0]="改ざん"
  with self.assertRaises(ValueError):update(m,a)
 def test_failed_update_does_not_mutate(self):
  m=make_session(10);a=update(m);before=deepcopy(a)
  bad=deepcopy(m);bad["turns"][0]["speaker"]="invalid"
  with self.assertRaises(ValueError):update(bad,a)
  self.assertEqual(a,before)
 def test_wrong_id(self):
  m=make_session(10);a=update(m);different=make_session(20)
  with self.assertRaises(ValueError):update(different,a)
 def test_checkpoint_reject(self):
  m=make_session(10);a=update(m);a["processed_turn"]=11
  with self.assertRaises(ValueError):update(m,a)
 def test_atomic_commit_replay(self):
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp)/"incremental.json";m=make_session(10)
   self.assertEqual(commit(m,path)["new_turns"],10)
   self.assertEqual(commit(m,path)["new_turns"],0)
   self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["processed_turn"],10)
 def test_no_eviction(self):
  m=make_session(10);a=update(m)
  self.assertFalse(a["approved_for_eviction"]);self.assertFalse(a["fact_promoted"])
 def test_benchmark(self):
  b=benchmark((10,20,30),3)
  self.assertTrue(all(row["equivalent_to_full"] for row in b["rows"]))
  self.assertEqual([row["new_turns"] for row in b["rows"]],[10,10,10])
 def test_invalid_checkpoints(self):
  with self.assertRaises(ValueError):benchmark((20,10))
  with self.assertRaises(ValueError):benchmark((0,))
 def test_benchmark_1000(self):
  b=benchmark((100,500,1000))
  self.assertTrue(all(r["equivalent_to_full"] for r in b["rows"]))
if __name__=="__main__":unittest.main()

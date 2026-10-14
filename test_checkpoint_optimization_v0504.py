import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from benchmark_long_conversation_resources_v042871 import make_session
from checkpoint_optimization_v0504 import update,commit,equivalent,benchmark,checksum

class CheckpointOptimizationTests(unittest.TestCase):
 def prefix(self,m,n):
  p=deepcopy(m);p["turns"]=deepcopy(m["turns"][:n]);p["last_turn"]=n
  p["sleep"]={"processed_turn":0,"completed":False};p["status"]="PENDING_SLEEP"
  return p
 def test_equivalence(self):
  m=make_session(100);a=update(self.prefix(m,30))
  self.assertTrue(equivalent(m,update(m,a)))
 def test_replay(self):
  m=make_session(20);a=update(m)
  self.assertEqual(update(m,a),a)
 def test_no_extract_old(self):
  m=make_session(20);a=update(self.prefix(m,10))
  self.assertEqual(update(m,a)["processed_turn"],20)
 def test_uncovered(self):
  m=make_session(30,3);a=update(m)
  self.assertTrue(equivalent(m,a))
  self.assertEqual(len(a["uncovered_turn_ids"]),10)
 def test_mutated_record(self):
  m=make_session(20);a=update(m);a["texts"][0]="tamper"
  with self.assertRaises(ValueError):update(m,a)
 def test_modified_source(self):
  m=make_session(20);a=update(m);changed=deepcopy(m)
  changed["turns"][0]["text"]="corrupted"
  with self.assertRaises(ValueError):update(changed,a)
 def test_wrong_id(self):
  m=make_session(20);a=update(m)
  with self.assertRaises(ValueError):update(make_session(21),a)
 def test_not_mutated_on_failure(self):
  m=make_session(20);a=update(m);old=deepcopy(a)
  bad=deepcopy(m);bad["turns"][0]["speaker"]="invalid"
  with self.assertRaises(ValueError):update(bad,a)
  self.assertEqual(a,old)
 def test_restart(self):
  with tempfile.TemporaryDirectory() as tmp:
   m=make_session(20);path=Path(tmp)/"checkpoint.json"
   r=commit(self.prefix(m,10),path)
   self.assertEqual(r["new_turns"],10)
   self.assertEqual(commit(m,path)["new_turns"],10)
   self.assertEqual(commit(m,path)["new_turns"],0)
   self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["processed_turn"],20)
 def test_no_deletion(self):
  a=update(make_session(10))
  self.assertFalse(a["approved_for_eviction"])
 def test_checksum(self):
  a=update(make_session(10))
  self.assertEqual(a["checkpoint_sha256"],checksum(a))
 def test_benchmark(self):
  r=benchmark((10,20),3,3)
  self.assertEqual(len(r["rows"]),2)
  self.assertTrue(all(x["equivalent_to_full"] for x in r["rows"]))
 def test_bad_benchmark(self):
  with self.assertRaises(ValueError):benchmark((20,10))
  with self.assertRaises(ValueError):benchmark((10,),repeats=1)
if __name__=="__main__":unittest.main()

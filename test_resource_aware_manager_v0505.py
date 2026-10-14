import unittest
from benchmark_long_conversation_resources_v042871 import make_session
from conversation_resource_memory_v042866 import sleep_checkpoint
from resource_aware_manager_v0505 import measure,plan,benchmark

class ResourceAwareTests(unittest.TestCase):
 def test_measure(self):
  x=measure(make_session(10))
  self.assertEqual(x["turns"],10)
  self.assertTrue(x["reconstructible"])
 def test_dry_run(self):
  x=benchmark((10,20))
  self.assertFalse(x["deletion_performed"])
  self.assertEqual(x["actual_bytes_freed"],0)
 def test_unique_id(self):
  m=make_session(10)
  with self.assertRaises(ValueError):plan([m,m],1000)
 def test_budget_zero(self):
  x=benchmark((10,),budget_bytes=0)
  self.assertTrue(x["source_over_budget"])
 def test_large_budget(self):
  x=benchmark((10,),budget_bytes=1000000)
  self.assertFalse(x["source_over_budget"])
 def test_active(self):
  m=make_session(10);m["active"]=True
  self.assertEqual(plan([m],0)["records"][0]["tier"],"HOT_ACTIVE")
 def test_pending(self):
  m=make_session(10)
  self.assertEqual(plan([m],0)["records"][0]["tier"],"WARM_PENDING_SLEEP")
 def test_uncovered(self):
  m=make_session(10,3)
  self.assertEqual(plan([m],0)["records"][0]["tier"],"WARM_UNCOVERED_PROTECTED")
 def test_completed(self):
  m=make_session(10);sleep_checkpoint(m,10,completed=True)
  self.assertEqual(plan([m],0)["records"][0]["tier"],"COLD_REVIEW_REQUIRED")
  self.assertFalse(plan([m],0)["records"][0]["deletion_allowed"])
 def test_inprogress(self):
  m=make_session(10);sleep_checkpoint(m,5)
  self.assertEqual(plan([m],0)["records"][0]["tier"],"HOT_SLEEP_IN_PROGRESS")
 def test_accounting(self):
  r=benchmark((10,20))
  self.assertEqual(r["projected_delta_bytes"],r["source_total_bytes"]-r["projected_compact_total_bytes"])
 def test_invalid(self):
  with self.assertRaises(ValueError):benchmark((0,))
  with self.assertRaises(ValueError):benchmark((10,),budget_bytes=-1)
if __name__=="__main__":unittest.main()

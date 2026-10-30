import unittest
from generation_attempt_tracker_v013588231 import AttemptTracker
class Tests(unittest.TestCase):
 def test_start_visible(self):
  t=AttemptTracker();key=t.start("宇宙")
  self.assertEqual(t.report()["attempts_started"],1)
  self.assertEqual(t.report()["in_flight"],1)
  self.assertEqual(t.attempts[key]["state"],"STARTED")
 def test_waiting_and_complete(self):
  t=AttemptTracker();key=t.start("宇宙")
  t.transition(key,"WAITING_LLM")
  self.assertEqual(t.report()["in_flight"],1)
  t.transition(key,"COMPLETED","REJECT_UNKNOWN")
  self.assertEqual(t.report()["completed"],1)
  self.assertEqual(t.report()["in_flight"],0)
 def test_failure(self):
  t=AttemptTracker();key=t.start("宇宙")
  t.transition(key,"FAILED","NO_MODEL")
  self.assertEqual(t.report()["failed"],1)
 def test_invalid(self):
  t=AttemptTracker()
  with self.assertRaises(KeyError):t.transition("bad","COMPLETED")
 def test_terminal_immutable(self):
  t=AttemptTracker();key=t.start("宇宙");t.transition(key,"COMPLETED")
  with self.assertRaises(ValueError):t.transition(key,"FAILED")
 def test_reset(self):
  t=AttemptTracker();t.start("宇宙");t.reset()
  self.assertEqual(t.report()["attempts_started"],0)
if __name__=="__main__":unittest.main()

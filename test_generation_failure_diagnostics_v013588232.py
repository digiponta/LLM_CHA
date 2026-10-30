import unittest
from generation_attempt_tracker_v013588231 import AttemptTracker

class Tests(unittest.TestCase):
 def test_failure_details(self):
  t=AttemptTracker();k=t.start("宇宙")
  t.annotate(k,failure_reason="SEND_FAILED",exception_type="ValueError",prompt_chars=102,process_alive=True)
  t.transition(k,"FAILED","SEND_FAILED")
  r=t.report()
  self.assertEqual(r["failure_reasons"]["SEND_FAILED"],1)
  self.assertEqual(r["recent_attempts"][0]["prompt_chars"],102)
  self.assertTrue(r["recent_attempts"][0]["process_alive"])
 def test_no_model(self):
  t=AttemptTracker();k=t.start("宇宙")
  t.annotate(k,failure_reason="NO_MODEL",process_alive=False)
  t.transition(k,"FAILED","NO_MODEL")
  self.assertEqual(t.report()["failure_reasons"]["NO_MODEL"],1)
 def test_in_flight(self):
  t=AttemptTracker();k=t.start("宇宙")
  t.transition(k,"WAITING_LLM")
  self.assertEqual(t.report()["in_flight"],1)
 def test_annotate_unknown_id(self):
  with self.assertRaises(KeyError):AttemptTracker().annotate("unknown",failure_reason="SEND_FAILED")
if __name__=="__main__":unittest.main()

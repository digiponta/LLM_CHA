import unittest
from followup_exhaustion_v074424 import FollowupExhaustion

class ExhaustionTests(unittest.TestCase):
    def test_first_then_clarify(self):
        f=FollowupExhaustion()
        self.assertIn("明確な根拠がない",f.respond("量子力学"))
        self.assertIn("基本原理、数式、実験、応用",f.respond("量子力学"))
    def test_topic_switch_resets(self):
        f=FollowupExhaustion()
        f.respond("量子力学")
        self.assertIn("明確な根拠がない",f.respond("CPU"))
    def test_explicit_reset(self):
        f=FollowupExhaustion()
        f.respond("量子力学")
        f.reset()
        self.assertIn("明確な根拠がない",f.respond("量子力学"))
    def test_no_topic(self):
        f=FollowupExhaustion()
        self.assertIsNone(f.respond(None))

if __name__=="__main__":
    unittest.main()

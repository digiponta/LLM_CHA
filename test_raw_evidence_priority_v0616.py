import unittest
from raw_evidence_priority_v0616 import conversational_intercept,allow_raw_evidence
class PriorityTests(unittest.TestCase):
    def test_persona_name_protected(self):
        self.assertFalse(allow_raw_evidence("長門","長門"))
    def test_second_person_intercept(self):
        self.assertIn("私について",conversational_intercept("貴方は"))
    def test_time_available(self):
        self.assertTrue(allow_raw_evidence("時間","時間"))
    def test_space_available(self):
        self.assertTrue(allow_raw_evidence("空間","空間"))
    def test_greeting_protected(self):
        self.assertFalse(allow_raw_evidence("こんにちは","こんにちは"))
    def test_normal_question_not_stolen(self):
        self.assertFalse(allow_raw_evidence("時間についてどう思う？","時間"))
if __name__=="__main__":unittest.main()

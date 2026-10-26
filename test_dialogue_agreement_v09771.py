import unittest
from dialogue_agreement_v09771 import AgreementContext
from semantic_dialogue_state_v09770 import extract_reason,extract_preference

class AgreementTests(unittest.TestCase):
    def test_reported_sequence(self):
        c=AgreementContext()
        c.record(extract_preference("私は、スファレライトが好きです。"))
        self.assertIsNone(c.reply("そうだよ"))
        c.record(extract_reason("きらきらしてるところが心地よい","スファレライト"))
        self.assertIn("スファレライト", c.reply("そうだよ"))
        self.assertIsNone(c.reply("そうだよ"))
    def test_no_context(self):
        self.assertIsNone(AgreementContext().reply("そうだよ"))
    def test_unrelated_turn_expires(self):
        c=AgreementContext()
        c.record(extract_reason("きらきらしてるところが心地よい","スファレライト"))
        self.assertIsNone(c.reply("屈折率は？"))
        self.assertIsNone(c.reply("そうだよ"))
    def test_no_command(self):
        c=AgreementContext()
        c.record(extract_reason("きらきらしてるところが心地よい","スファレライト"))
        self.assertIsNone(c.reply("/sleep"))

if __name__=="__main__":
    unittest.main()

import unittest
from preference_dialogue_v09768 import PreferenceDialogue

class SensoryPreferenceTests(unittest.TestCase):
    def test_reported_gui_sequence(self):
        dialogue = PreferenceDialogue()
        self.assertIn("スファレライト", dialogue.reply("私は、スファレライトが好きです。"))
        reply = dialogue.reply("きらきらしてるところが心地よい")
        self.assertIn("スファレライト", reply)
        self.assertIn("きらきら", reply)
        self.assertIn("心地よい", reply)

    def test_followup_is_one_turn(self):
        dialogue = PreferenceDialogue()
        dialogue.reply("スファレライトが好きです")
        dialogue.reply("きらきらしてるところが心地よい")
        self.assertIsNone(dialogue.reply("心地よい"))

    def test_question_interrupts(self):
        dialogue = PreferenceDialogue()
        dialogue.reply("スファレライトが好きです")
        self.assertIsNone(dialogue.reply("屈折率は？"))
        self.assertIsNone(dialogue.reply("きらきらしてるところが心地よい"))

    def test_no_unprompted_claim(self):
        self.assertIsNone(PreferenceDialogue().reply("きらきらしてるところが心地よい"))

if __name__ == "__main__":
    unittest.main()

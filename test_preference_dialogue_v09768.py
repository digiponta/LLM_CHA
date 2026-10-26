import unittest
from preference_dialogue_v09768 import PreferenceDialogue

class PreferenceDialogueTests(unittest.TestCase):
    def test_followup(self):
        d=PreferenceDialogue()
        self.assertIn("スファレライト", d.reply("私は、スファレライトが好きです"))
        self.assertIn("スファレライト", d.reply("きれいだから"))
    def test_followup_is_consumed(self):
        d=PreferenceDialogue()
        d.reply("スファレライトが好きです")
        d.reply("きれいです")
        self.assertIsNone(d.reply("きれいです"))
    def test_clear_on_unrelated(self):
        d=PreferenceDialogue()
        d.reply("スファレライトが好きです")
        self.assertIsNone(d.reply("屈折率は？"))
        self.assertIsNone(d.reply("きれいです"))
    def test_no_pref_storage(self):
        d=PreferenceDialogue()
        self.assertIsNone(d.reply("/sleep"))
    def test_topic_switch(self):
        d=PreferenceDialogue()
        d.reply("スファレライトが好きです")
        self.assertIn("ダイヤモンド", d.reply("ダイヤモンドが好きです"))
        self.assertIn("ダイヤモンド", d.reply("美しいから"))
if __name__=="__main__":
    unittest.main()

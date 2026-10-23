import unittest
from synonym_recovery_v07448 import recover_bare_synonym

class Lexicon:
    def expand(self, term):
        return [term, "ネコ"] if term == "ぬこ" else [term]

class RecoveryTests(unittest.TestCase):
    def test_recover(self):
        r=recover_bare_synonym("ぬこ",Lexicon(),lambda t:{"status":"FOUND","answer":"猫の説明","source":"wiki-url"},lambda t:True)
        self.assertEqual(r["term"],"ネコ")
        self.assertFalse(r["train_ready"])
    def test_blocked_source(self):
        self.assertIsNone(recover_bare_synonym("ぬこ",Lexicon(),lambda t:{"status":"FOUND","answer":"x","source":"url"},lambda t:t!="ネコ"))
    def test_not_question(self):
        self.assertIsNone(recover_bare_synonym("ぬことは",Lexicon(),lambda t:None,lambda t:True))
    def test_unavailable(self):
        self.assertIsNone(recover_bare_synonym("ぬこ",Lexicon(),lambda t:{"status":"NOT_FOUND"},lambda t:True))
    def test_command_protected(self):
        self.assertIsNone(recover_bare_synonym("/sleep",Lexicon(),lambda t:None,lambda t:True))

if __name__=="__main__":
    unittest.main()

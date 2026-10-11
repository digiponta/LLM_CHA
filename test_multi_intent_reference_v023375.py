import unittest
from multi_intent_reference_v023375 import split_input,clarify_reference

class MultiIntentTests(unittest.TestCase):
    def test_greeting_knowledge(self):
        self.assertEqual(split_input("こんにちは、宇宙について教えて"),("宇宙とは","GREETING_PLUS_KNOWLEDGE"))
    def test_kb_variant(self):
        self.assertEqual(split_input("こんばんは、量子力学とは"),("量子力学とは","GREETING_PLUS_KNOWLEDGE"))
    def test_reference_yesterday(self):
        self.assertEqual(split_input("昨日の続き"),("昨日の続き","REFERENCE_CLARIFY"))
    def test_reference_old_experiment(self):
        self.assertEqual(split_input("あの実験"),("あの実験","REFERENCE_CLARIFY"))
    def test_clarification_has_no_claim(self):
        self.assertIn("どの実験",clarify_reference())
    def test_standalone_greeting_untouched(self):
        self.assertEqual(split_input("こんにちは"),("こんにちは",None))
    def test_standalone_concept_untouched(self):
        self.assertEqual(split_input("宇宙とは"),("宇宙とは",None))
    def test_command_untouched(self):
        self.assertEqual(split_input("/truth 宇宙"),("/truth 宇宙",None))
    def test_mixed_not_overbroad(self):
        self.assertEqual(split_input("こんにちは、宇宙について教えて、それと時間も"),("こんにちは、宇宙について教えて、それと時間も",None))
    def test_no_injection_to_reference(self):
        self.assertEqual(split_input("昨日の続きで宇宙について教えて"),("昨日の続きで宇宙について教えて",None))
    def test_no_silent_truth_assignment(self):
        self.assertEqual(split_input("こんにちは、宇宙について教えてください")[0],"宇宙とは")
if __name__=="__main__":unittest.main()

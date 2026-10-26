import unittest
from unittest.mock import Mock
from temporary_evidence_retriever_v0137 import retrieve,answer_from_evidence
from chat_gui_v0119 import ChatGUI

SOURCE="スファレライトは硫化亜鉛（ZnS）を主成分とする鉱物です。スファレライトの屈折率は2.37程度です。"

class TemporaryEvidenceTests(unittest.TestCase):
    def test_grounded_extract(self):
        self.assertIn("硫化亜鉛",answer_from_evidence(SOURCE,"スファレライトの成分は何ですか"))
    def test_unrelated_does_not_hallucinate(self):
        self.assertIsNone(answer_from_evidence(SOURCE,"火星の衛星について教えて"))
    def test_no_chitchat_hijack(self):
        self.assertIsNone(answer_from_evidence(SOURCE,"今日はいい天気ですね"))
    def test_no_evidence(self):
        self.assertEqual(retrieve("","スファレライトの成分は"),[])
    def test_original_text_not_generated(self):
        hits=retrieve(SOURCE,"スファレライトの成分は何ですか")
        self.assertTrue(hits)
        self.assertTrue(all(h.text in SOURCE for h in hits))
    def test_gui_generic_evidence_query(self):
        gui=ChatGUI.__new__(ChatGUI)
        gui.entry=Mock();gui._append=Mock();gui.submit=Mock()
        gui.clipboard_context=SOURCE;gui.last_clipboard_source=SOURCE
        gui.active_food_item="";gui.active_preference_topic=""
        gui.entry.get.return_value="スファレライトの成分は何ですか"
        gui.send()
        self.assertIn("硫化亜鉛",gui._append.call_args.args[0])
        gui.submit.assert_not_called()

if __name__=="__main__":
    unittest.main()

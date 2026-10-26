import unittest
from unittest.mock import Mock
from evidence_topic_context_v0138 import EvidenceTopicContext
from chat_gui_v0119 import ChatGUI

SOURCE=("スファレライトの化学組成は硫化亜鉛（ZnS）です。"
        "スファレライトの屈折率は約2.37です。")

class EvidenceTopicV0138Tests(unittest.TestCase):
    def test_three_turn_subject_attribute_reference(self):
        ctx=EvidenceTopicContext()
        self.assertIn("硫化亜鉛",ctx.answer(SOURCE,"スファレライトの化学組成は？"))
        self.assertIn("2.37",ctx.answer(SOURCE,"屈折率は？"))
        comparison=ctx.answer(SOURCE,"それは高いの？")
        self.assertIn("比較基準",comparison)
        self.assertIn("未検証",comparison)
        self.assertEqual((ctx.state.subject,ctx.state.attribute),("スファレライト","屈折率"))

    def test_no_prior_subject_no_answer(self):
        ctx=EvidenceTopicContext()
        self.assertIsNone(ctx.answer(SOURCE,"屈折率は？"))
        self.assertIsNone(ctx.answer(SOURCE,"それは高いの？"))

    def test_missing_evidence_does_not_claim_value(self):
        ctx=EvidenceTopicContext()
        short_source="スファレライトの化学組成はZnSです。"
        self.assertIn("ZnS",ctx.answer(short_source,"スファレライトの化学組成は？"))
        self.assertIn("確認できません",ctx.answer(short_source,"屈折率は？"))
        comparison=ctx.answer(short_source,"それは高いの？")
        self.assertIn("スファレライトの屈折率",comparison)
        self.assertIn("比較基準",comparison)
        self.assertIn("未検証",comparison)

    def test_gui_missing_evidence_followup(self):
        short_source="スファレライトの化学組成は硫化亜鉛（ZnS）です。"
        gui=ChatGUI.__new__(ChatGUI)
        gui.entry=Mock()
        gui._append=Mock()
        gui.submit=Mock()
        gui.clipboard_context=short_source
        gui.last_clipboard_source=short_source
        gui.active_preference_topic=""
        gui.active_food_item=""
        gui.evidence_topic_context=EvidenceTopicContext()
        for msg in ("スファレライトの化学組成は？","屈折率は？","それは高いの？"):
            gui.entry.get.return_value=msg
            gui.send()
        self.assertEqual(gui._append.call_count,3)
        self.assertIn("比較基準",gui._append.call_args.args[0])
        self.assertIn("スファレライトの屈折率",gui._append.call_args.args[0])

    def test_new_source_resets_previous_reference(self):
        ctx=EvidenceTopicContext()
        ctx.answer(SOURCE,"スファレライトの屈折率は？")
        self.assertIsNone(ctx.answer("石英の屈折率は約1.54です。","それは高いの？"))
        self.assertEqual(ctx.state.subject,"")

    def test_unrelated_chat_does_not_take_over(self):
        ctx=EvidenceTopicContext()
        ctx.answer(SOURCE,"スファレライトの屈折率は？")
        self.assertIsNone(ctx.answer(SOURCE,"今日は楽しいです"))
        self.assertEqual(ctx.state.subject,"スファレライト")

    def test_gui_three_turn_integration(self):
        gui=ChatGUI.__new__(ChatGUI)
        gui.entry=Mock()
        gui._append=Mock()
        gui.submit=Mock()
        gui.clipboard_context=SOURCE
        gui.last_clipboard_source=SOURCE
        gui.active_preference_topic=""
        gui.active_food_item=""
        gui.evidence_topic_context=EvidenceTopicContext()
        for message in ("スファレライトの化学組成は？","屈折率は？","それは高いの？"):
            gui.entry.get.return_value=message
            gui.send()
        self.assertEqual(gui._append.call_count,3)
        self.assertIn("比較基準",gui._append.call_args.args[0])
        gui.submit.assert_not_called()

    def test_gui_no_evidence_fabrication(self):
        gui=ChatGUI.__new__(ChatGUI)
        gui.entry=Mock()
        gui._append=Mock()
        gui.submit=Mock()
        gui.clipboard_context=SOURCE
        gui.last_clipboard_source=SOURCE
        gui.active_preference_topic=""
        gui.active_food_item=""
        gui.evidence_topic_context=EvidenceTopicContext()
        gui.entry.get.return_value="スファレライトの屈折率は？"
        gui.send()
        self.assertIn("2.37",gui._append.call_args.args[0])
        self.assertIn("未検証",gui._append.call_args.args[0])

if __name__=="__main__":
    unittest.main()

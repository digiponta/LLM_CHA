import unittest
from extended_chat_runtime_v023378 import BASE_CASES, CASES, evaluate

def success_transcript():
    return (
        "intro\nYou> AI> こんにちは。\n[response-quality=REPAIRED, intent=greeting]\n"
        "You> [multi-intent=GREETING_PLUS_KNOWLEDGE]\n[truth-aware-corpus=BLOCK]\nAI> 未学習です\n"
        "You> [truth-aware-corpus=BLOCK]\nAI> 未学習です\n"
        "You> AI> どの実験・話題の続きでしょうか？\n[multi-intent=REFERENCE_CLARIFY]\n"
        "You> AI> どの実験・話題の続きでしょうか？\n[multi-intent=REFERENCE_CLARIFY]\n"
        "You> [multi-intent=GREETING_PLUS_KNOWLEDGE]\n[truth-aware-corpus=BLOCK]\nAI> 未学習です\n"
        "You> AI> こんにちは。\n[gate=KNOWN,intent=greeting]\n"
        "You> AI> どういたしまして。\nYou> "
    )
class ExtendedRuntimeTests(unittest.TestCase):
    def test_fixed_baseline_preserved(self):
        self.assertEqual(len(BASE_CASES),4)
        self.assertEqual(len(CASES),8)
    def test_separates_answer_and_route(self):
        r=evaluate(success_transcript(),0)
        self.assertTrue(r["acceptance_pass"])
        self.assertEqual(r["acceptance_matched"],5)
        self.assertEqual(r["exploratory_total"],3)
        self.assertIsNone(r["cases"][-1]["answer_pass"])
    def test_wrong_answer_does_not_pass(self):
        r=evaluate(success_transcript().replace("AI> こんにちは。","AI> 別の回答",1),0)
        self.assertFalse(r["acceptance_pass"])
        self.assertTrue(r["cases"][0]["route_pass"])
        self.assertFalse(r["cases"][0]["answer_pass"])
    def test_nonzero_process_fails(self):
        self.assertFalse(evaluate(success_transcript(),1)["acceptance_pass"])
    def test_short_transcript_unobserved(self):
        r=evaluate("You> AI> こんにちは。\n",0)
        self.assertFalse(r["acceptance_pass"])
        self.assertFalse(r["cases"][-1]["observed"])
if __name__=="__main__":unittest.main()

import tempfile,unittest
from pathlib import Path
from chat_runtime_benchmark_v023377 import SCENARIOS,evaluate_transcript,ensure_source,isolated_copy

class ChatRuntimeBenchmarkTests(unittest.TestCase):
    def test_four_scenarios(self):
        self.assertEqual(len(SCENARIOS),4)
    def test_piped_stdin_without_echo(self):
        transcript=(
            "startup\nYou> AI> こんにちは。\n[response-quality=REPAIRED]\n"
            "You> [multi-intent=GREETING_PLUS_KNOWLEDGE]\n[truth-aware-corpus=BLOCK]\n"
            "You> [truth-aware-corpus=BLOCK]\nAI> 未学習です\n"
            "You> AI> どの実験・話題の続きでしょうか？\n[multi-intent=REFERENCE_CLARIFY]\n"
            "You> ")
        result=evaluate_transcript(transcript,0)
        self.assertEqual(result["passed"],4,result)
    def test_short_transcript_not_false_pass(self):
        r=evaluate_transcript("You> AI> こんにちは。\n[response-quality=REPAIRED]\n",0)
        self.assertEqual(r["passed"],1)
        self.assertEqual(r["total"],4)
    def test_policy_violation_detected(self):
        transcript="You> AI> 宇宙はすばらしい\nYou> AI> 宇宙の説明\nYou> AI> 宇宙は大きい\nYou> AI> 分かりません"
        self.assertEqual(evaluate_transcript(transcript,0)["passed"],0)
    def test_bad_checkout_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):ensure_source(d)
    def test_copy_is_independent(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/"src";root.mkdir()
            (root/"chat.py").write_text("x=1\n",encoding="utf8")
            (root/"model").mkdir();(root/"data").mkdir()
            (root/"data"/"demo.txt").write_text("old",encoding="utf8")
            target=Path(d)/"out"
            isolated_copy(root,target)
            (target/"data"/"demo.txt").write_text("new",encoding="utf8")
            self.assertEqual((root/"data"/"demo.txt").read_text(encoding="utf8"),"old")
if __name__=="__main__":unittest.main()

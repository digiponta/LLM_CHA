import unittest
from diagnose_raw_runtime_v02271 import extract_runtime

class RuntimeLogTests(unittest.TestCase):
    def test_parse(self):
        rows = extract_runtime("You> 宇宙探査\nAI> そう。\n[gate=KNOWN]\nYou> 陶芸\nAI> 未学習です\n")
        self.assertEqual(rows, [{"prompt":"宇宙探査","runtime_answer":"そう。"},{"prompt":"陶芸","runtime_answer":"未学習です"}])

    def test_missing_runtime(self):
        self.assertEqual(extract_runtime("You> 質問\n[gate=UNKNOWN]"), [])

if __name__ == "__main__":
    unittest.main()

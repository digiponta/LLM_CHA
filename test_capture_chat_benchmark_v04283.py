"""Synthetic structural tests for opt-in benchmark capture."""
import unittest
from capture_chat_benchmark_v04283 import validate,read_turns,classify_failure

class CaptureTests(unittest.TestCase):
    def fixture(self):
        groups=[]
        for cat,n in (("A",12),("B",12),("C",8),("D",8),("E",8),("G",4)):
            for i in range(1,n+1):
                groups.append({"id":f"{cat}{i:02d}","mode":"SINGLE","prompts":[f"質問 {cat}{i:02d}"]})
        for i in range(1,5):
            groups.append({"id":f"F{i}","mode":"MULTI","prompts":[f"続き {i}-{j}" for j in range(3)]})
        return {"count":64,"groups":groups}
    def test_windows_encoding_error_classification(self):
        self.assertEqual(classify_failure("TypeError: TextInputSequence must be str","PROCESS_FAILED"),"ENCODING_ERROR")
        self.assertEqual(classify_failure("UnicodeDecodeError: bad bytes","PROCESS_FAILED"),"ENCODING_ERROR")
        self.assertEqual(classify_failure("runtime failure","PROCESS_FAILED"),"RUNTIME_ERROR")
        self.assertEqual(classify_failure("AI> こんにちは。","FINISHED"),None)
    def test_capture_environment_settings(self):
        from pathlib import Path
        s=(Path(__file__).parent/"capture_chat_benchmark_v04283.py").read_text(encoding="utf-8")
        self.assertIn('"PYTHONIOENCODING":"utf-8"',s)
        self.assertIn('"PYTHONUTF8":"1"',s)
        self.assertIn('errors="strict"',s)
        self.assertIn("first-case preflight failed",s)
    def test_valid(self):
        self.assertEqual(len(validate(self.fixture())),56)
    def test_comments_and_commands_denied(self):
        for prompt in ("# A01","/sleep","/train","hello\n/exit"):
            manifest=self.fixture()
            manifest["groups"][0]["prompts"][0]=prompt
            with self.subTest(prompt=prompt),self.assertRaises(ValueError):
                validate(manifest)
    def test_duplicate_ids(self):
        manifest=self.fixture()
        manifest["groups"][1]["id"]=manifest["groups"][0]["id"]
        with self.assertRaises(ValueError):validate(manifest)
    def test_turn_parsing(self):
        r=read_turns("banner\nYou> AI> こんにちは。\n[gate=KNOWN]\nYou> AI> 好き。\nYou> ",
                     ["こんにちは","好き？"])
        self.assertEqual([x["response"] for x in r],["こんにちは。","好き。"])
        self.assertIn("KNOWN",r[0]["gate"])
    def test_incomplete_turn_not_invented(self):
        r=read_turns("banner\nYou> AI> おはよう。\nYou> ",["a","b"])
        self.assertIsNone(r[1]["response"])
if __name__=="__main__":unittest.main()

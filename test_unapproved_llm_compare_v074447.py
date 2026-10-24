import tempfile
import unittest
from pathlib import Path
from unapproved_llm_intake_v074446 import ingest_wikipedia
from unapproved_llm_compare_v074447 import unapproved_answer,compare_answers

WIKI={"status":"FOUND","title":"量子ビット",
"url":"https://ja.wikipedia.org/wiki/量子ビット",
"extract":"量子ビットは量子情報科学および量子コンピュータにおいて情報を表現するための基本単位である。"}
class CompareTests(unittest.TestCase):
    def test_grounded_unapproved_answer(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"candidates.json"
            self.assertEqual(ingest_wikipedia(WIKI,path)["status"],"STORED")
            response=unapproved_answer("量子ビットとは",path)
            self.assertEqual(response["status"],"FOUND")
            self.assertFalse(response["model_generated"])
            self.assertFalse(response["train_ready"])
            self.assertEqual(response["source"],WIKI["url"])
    def test_missing_candidate(self):
        with tempfile.TemporaryDirectory() as folder:
            self.assertEqual(unapproved_answer("量子ビットとは",Path(folder)/"empty.json")["status"],"NO_MATCH")
    def test_no_promotion(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"candidates.json"
            ingest_wikipedia(WIKI,path)
            result=compare_answers("量子ビットとは","承認済み回答",path)
            self.assertFalse(result["approved_memory_changed"])
            self.assertFalse(result["weights_changed"])
            self.assertIsNone(result["preferred"])
    def test_chat_command(self):
        src=Path(__file__).with_name("chat.py").read_text(encoding="utf-8")
        self.assertIn('user_text.startswith("/wiki-compare ")',src)
if __name__=="__main__": unittest.main()

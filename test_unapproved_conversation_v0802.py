import tempfile
import unittest
from pathlib import Path
from unapproved_llm_intake_v074446 import _save
from unapproved_conversation_v0802 import parse_unapproved_request,conversational_answer

class UnapprovedConversationTests(unittest.TestCase):
    def test_explicit_opt_in(self):
        self.assertEqual(parse_unapproved_request("未承認知識で量子ビットとは"),"量子ビットとは")
        self.assertIsNone(parse_unapproved_request("量子ビットとは"))
    def test_grounded_dialogue(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"store.json"
            _save(path,{"candidates":[{"id":"x","subject":"量子ビット","natural_language":"量子ビットは量子情報の基本単位である。",
                "source":"https://ja.wikipedia.org/wiki/量子ビット","state":"UNAPPROVED",
                "truth_state":"EXTERNAL_UNVERIFIED",
                "semantic_candidate":{"status":"STRUCTURED","subject":"量子ビット","relation":"is_basic_unit","object":"基本単位"}}]})
            result=conversational_answer("量子ビットとは",path)
            self.assertEqual(result["status"],"FOUND")
            self.assertIn("出典：",result["answer"])
            self.assertFalse(result["train_ready"])
    def test_no_fake_answer(self):
        with tempfile.TemporaryDirectory() as folder:
            result=conversational_answer("量子ビットとは",Path(folder)/"none.json")
            self.assertNotEqual(result["status"],"FOUND")
    def test_runtime_wiring(self):
        source=Path(__file__).with_name("chat.py").read_text(encoding="utf-8")
        self.assertIn("parse_unapproved_request(user_text)",source)
if __name__=="__main__":unittest.main()

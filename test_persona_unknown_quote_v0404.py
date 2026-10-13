import tempfile
import unittest
from pathlib import Path
from persona_unknown_quote_v0404 import unknown_persona_quote

class UnknownPersonaQuoteTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.source=Path(self.tmp.name)/"corpus.txt"
        self.source.write_text("数学は、文学の分類。\n量子力学について考える。",encoding="utf-8")
    def tearDown(self):self.tmp.cleanup()
    def test_literature_is_related_not_definition(self):
        row=unknown_persona_quote(self.source,"文学とは","文学")
        self.assertIn("数学は、文学の分類",row["answer"])
        self.assertIn("定義として検証された内容ではありません",row["answer"])
        self.assertEqual(row["factual_truth"],"NOT_ASSESSED")
    def test_missing_novel_no_quote(self):
        self.assertIsNone(unknown_persona_quote(self.source,"小説とは","小説"))
    def test_unrelated_prompt_rejected(self):
        self.assertIsNone(unknown_persona_quote(self.source,"文学で何を学ぶ？","文学"))
    def test_wrong_focus_rejected(self):
        self.assertIsNone(unknown_persona_quote(self.source,"数学とは","文学"))
    def test_no_mutation(self):
        original=self.source.read_bytes()
        unknown_persona_quote(self.source,"文学とは","文学")
        self.assertEqual(original,self.source.read_bytes())
    def test_chat_wiring_and_truth_guard(self):
        s=Path("chat.py").read_text(encoding="utf-8")
        self.assertIn("LLM_CHA_UNKNOWN_PERSONA_QUOTE",s)
        self.assertIn('dispatch.state == "UNKNOWN"',s)
        self.assertIn("truth_allows_direct_retrieval(unknown_truth.state)",s)
        self.assertIn("not force_internalized_verification",s)
    def test_default_off(self):
        s=Path("chat.py").read_text(encoding="utf-8")
        self.assertIn('os.environ.get("LLM_CHA_UNKNOWN_PERSONA_QUOTE", "0") == "1"',s)
if __name__=="__main__":unittest.main()

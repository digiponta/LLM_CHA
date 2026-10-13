import tempfile
import unittest
from pathlib import Path
from persona_routing_v0374 import answer_prefix,is_persona_corpus,ranked_persona_reply

class PersonaRoutingTests(unittest.TestCase):
    def test_nagato_corpus(self):
        self.assertEqual(answer_prefix("data-nagato.txt:subject-keyed-corpus-memory:v10.12.16"),"persona>")
    def test_windows_path(self):
        self.assertTrue(is_persona_corpus(r"C:\\data\\data-nagato.txt:subject-keyed-corpus-memory:v10.12.16"))
    def test_canonical_stays_ai(self):
        self.assertEqual(answer_prefix("chat.py:CANONICAL_DEFINITIONS"),"AI>")
    def test_other_corpus_stays_ai(self):
        self.assertEqual(answer_prefix("other.txt:subject-keyed-corpus-memory"),"AI>")
    def test_rank_long_sentence_over_fragment(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"raw.txt"
            p.write_text("数学的に証明される。\n数学はこの世界の様々な現象を記述し表現するための体系である。",encoding="utf-8")
            result,rows=ranked_persona_reply(p,"数学",1)
            self.assertIn("数学はこの世界",result)
            self.assertEqual(rows[0].line,2)
    def test_empty_evidence(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"raw.txt";p.write_text("宇宙。",encoding="utf-8")
            self.assertEqual(ranked_persona_reply(p,"数学"),(None,[]))
    def test_chat_wiring(self):
        code=Path("chat.py").read_text(encoding="utf-8")
        self.assertIn("answer_prefix(followup_hit.provenance)",code)
        self.assertIn("answer_prefix(retrieval.provenance)",code)
        self.assertIn("ranked_persona_reply(",code)
    def test_truth_gate_unchanged(self):
        code=Path("chat.py").read_text(encoding="utf-8")
        self.assertIn("truth_allows_direct_retrieval(",code)
        self.assertIn('dispatch.state == "RAW_CORPUS_ONLY"',code)

if __name__=="__main__":unittest.main()

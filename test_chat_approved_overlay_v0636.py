"""v0.6.36 opt-in approved QA chat wiring regressions."""
import ast
import json
import tempfile
import unittest
from pathlib import Path
from evaluate_memory_first_v0635 import load_overlay, norm

class ChatApprovedOverlayTests(unittest.TestCase):
    def test_chat_source_compiles(self):
        ast.parse(Path("chat.py").read_text(encoding="utf-8"))
    def test_opt_in_only_and_pre_generation(self):
        content=Path("chat.py").read_text(encoding="utf-8")
        self.assertIn('parser.add_argument("--approved-qa-overlay", default=None',content)
        self.assertIn('if not user_text.startswith("/") and approved_qa_overlay:',content)
        self.assertIn('memory_hit["route"]',content)
        self.assertLess(content.index('memory_hit = approved_qa_lookup(user_text, approved_qa_overlay, synonym_lexicon)'),
                        content.index('# Explicit Japanese synonym declarations'))
    def test_reviewed_fact_loaded_and_unapproved_excluded(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"approved.jsonl"
            p.write_text("\n".join(json.dumps(row,ensure_ascii=False) for row in [
                {"question":"  合言葉は何ですか  ","answer":"検証用です。","status":"approved","source_id":"review:1"},
                {"question":"禁止","answer":"採用しない","status":"pending","source_id":"review:2"}]),encoding="utf-8-sig")
            records=load_overlay(p)
            self.assertEqual(records[norm("合言葉は何ですか")]["source_id"],"review:1")
            self.assertNotIn("禁止",records)
    def test_no_training_side_effect_in_overlay_module(self):
        src=Path("evaluate_memory_first_v0635.py").read_text(encoding="utf-8")
        self.assertNotIn("optimizer.step(",src)
if __name__=="__main__":unittest.main()

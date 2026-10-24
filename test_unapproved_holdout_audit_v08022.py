import json
import tempfile
import unittest
from pathlib import Path
from unapproved_holdout_audit_v08022 import audit
from unapproved_llm_intake_v074446 import _save

class HoldoutAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.store=self.root/"store.json"
        self.holdout=self.root/"holdout.json"
        _save(self.store,{"candidates":[{"id":"trained","subject":"量子ビット",
            "natural_language":"量子ビットは量子情報の基本単位である。"}]})
    def write(self,records):
        self.holdout.write_text(json.dumps({"records":records,"independent_source_attested":False},
                                           ensure_ascii=False),encoding="utf-8")
    def test_missing(self):
        self.assertEqual(audit(self.holdout,self.store)["status"],"MISSING_DATA")
    def test_overlap_warning(self):
        self.write([{"id":"new1","evaluation_kind":"UNSEEN_FACT",
            "question":"量子ビットの性質は？",
            "reference_answer":"量子ビットは量子情報の基本単位である。",
            "source_url":"https://example.org/a","source_excerpt":"原文"}])
        result=audit(self.holdout,self.store)
        self.assertIn("LEXICAL_ANSWER_OVERLAP",result["details"][0]["flags"])
        self.assertIn("TRAINED_SUBJECT_IN_UNSEEN_FACT",result["details"][0]["flags"])
        self.assertFalse(result["semantic_independence_verified"])
    def test_distinct_groups(self):
        self.write([{"id":"new2","evaluation_kind":"PARAPHRASE",
            "question":"別の表現で尋ねる","reference_answer":"別の根拠文",
            "source_url":"https://example.org/b","source_excerpt":"原文"}])
        result=audit(self.holdout,self.store)
        self.assertEqual(result["kind_counts"]["PARAPHRASE"],1)
        self.assertFalse(result["usable_for_formal_evaluation"])
    def test_gui_command(self):
        gui=Path(__file__).with_name("chat_gui_v07447.py").read_text(encoding="utf-8")
        chat=Path(__file__).with_name("chat.py").read_text(encoding="utf-8")
        self.assertIn('request_status("/wiki-model-holdout-audit")',gui)
        self.assertIn('if user_text == "/wiki-model-holdout-audit":',chat)
if __name__=="__main__":unittest.main()

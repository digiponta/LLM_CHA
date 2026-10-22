import ast
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from synonym_lexicon_v0626 import SynonymLexicon
from approved_synonym_qa_v0637 import approved_qa_lookup

class ApprovedSynonymQA(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory()
        self.lex=SynonymLexicon(Path(self.tmp.name)/"synonyms.jsonl")
    def tearDown(self):
        self.tmp.cleanup()
    def test_direct_priority(self):
        store={"猫とは":{"answer":"猫です。","source_id":"a"},
               "ネコとは":{"answer":"ネコです。","source_id":"b"}}
        r=approved_qa_lookup("猫とは",store,self.lex)
        self.assertEqual(r["route"],"APPROVED_QA_OVERLAY")
        self.assertEqual(r["answer"],"猫です。")
    def test_synonym_expansion(self):
        store={"ネコとは":{"answer":"ネコは動物です。","source_id":"review-1"}}
        r=approved_qa_lookup("猫とは",store,self.lex)
        self.assertEqual(r["route"],"APPROVED_SYNONYM_QA")
        self.assertEqual(r["source_id"],"review-1")
        self.assertEqual(r["matched_question"],"ネコとは")
    def test_unregistered_related_not_alias(self):
        store={"犬とは":{"answer":"犬です","source_id":"a"}}
        self.assertIsNone(approved_qa_lookup("猫とは",store,self.lex))
    def test_disagreement_rejected(self):
        store={"ネコとは":{"answer":"回答1","source_id":"a"},
               "ねことは":{"answer":"回答2","source_id":"b"}}
        self.assertIsNone(approved_qa_lookup("猫とは",store,self.lex))
    def test_unmatched_falls_through(self):
        self.assertIsNone(approved_qa_lookup("地球とは",{},self.lex))
    def test_chat_compiles_and_routes_before_generation(self):
        source=Path("chat.py").read_text(encoding="utf-8")
        ast.parse(source)
        self.assertIn("approved_qa_lookup(user_text, approved_qa_overlay, synonym_lexicon)",source)
        self.assertIn('if not user_text.startswith("/") and approved_qa_overlay:',source)
    def test_lexicon_unmodified(self):
        before=dict((k,set(v)) for k,v in self.lex.edges.items())
        approved_qa_lookup("猫とは",{"ネコとは":{"answer":"動物","source_id":"a"}},self.lex)
        self.assertEqual(self.lex.edges,before)

if __name__=="__main__":unittest.main()

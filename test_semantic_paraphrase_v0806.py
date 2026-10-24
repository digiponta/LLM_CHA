import tempfile
import unittest
from pathlib import Path
from unapproved_llm_intake_v074446 import _save
from unapproved_semantic_search_v0801 import search_semantic

class ParaphraseSemanticTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path=Path(self.folder.name)/"store.json"
        _save(self.path,{"candidates":[{"id":"qubit1","subject":"量子ビット",
            "natural_language":"量子ビットは量子情報の基本単位である。",
            "source":"https://ja.wikipedia.org/wiki/量子ビット",
            "state":"UNAPPROVED","truth_state":"EXTERNAL_UNVERIFIED",
            "semantic_candidate":{"status":"STRUCTURED","subject":"量子ビット",
                                  "relation":"is_basic_unit","object":"基本単位"}}]})
    def test_paraphrase(self):
        for q in ("量子ビットはどういうもの？","量子ビットについて教えて","量子ビットを説明して"):
            with self.subTest(q=q):
                self.assertEqual(search_semantic(q,self.path)["status"],"FOUND")
    def test_unrelated_subject_rejected(self):
        self.assertEqual(search_semantic("古典ビットについて教えて",self.path)["status"],"NO_STRUCTURED_MATCH")
    def test_no_unrelated_relation(self):
        self.assertEqual(search_semantic("量子ビットの価格はいくら",self.path)["status"],"NO_STRUCTURED_MATCH")
    def test_provenance_kept(self):
        result=search_semantic("量子ビットについて教えて",self.path)
        self.assertFalse(result["train_ready"])
        self.assertEqual(result["truth_state"],"EXTERNAL_UNVERIFIED")
        self.assertEqual(result["candidate_id"],"qubit1")

if __name__=="__main__":unittest.main()

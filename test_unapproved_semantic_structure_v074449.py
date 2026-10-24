import tempfile
import unittest
from pathlib import Path
from unapproved_semantic_structure_v074449 import extract_structure
from unapproved_llm_intake_v074446 import ingest_wikipedia,inspect_candidates

class SemanticStructureTests(unittest.TestCase):
    def test_explicit_relation(self):
        result=extract_structure("量子ビットは重ね合わせ状態をとることができる。","量子ビット")
        self.assertEqual(result["status"],"STRUCTURED")
        self.assertEqual(result["relation"],"can_take_state")
        self.assertEqual(result["object"],"重ね合わせ状態")
    def test_no_inferred_pronoun(self):
        result=extract_structure("それは重ね合わせ状態をとることができる。","量子ビット")
        self.assertEqual(result["status"],"UNSTRUCTURED")
    def test_persist_source_and_structure(self):
        article={"status":"FOUND","title":"量子ビット",
                 "url":"https://ja.wikipedia.org/wiki/量子ビット",
                 "extract":"量子ビットは量子力学に基づく重ね合わせ状態をとることができる。"}
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"unapproved.json"
            result=ingest_wikipedia(article,path)
            self.assertEqual(result["status"],"STORED")
            item=inspect_candidates(path)["candidates"][0]
            self.assertEqual(item["semantic_candidate"]["status"],"STRUCTURED")
            self.assertEqual(item["truth_state"],"EXTERNAL_UNVERIFIED")
            self.assertFalse(item["train_ready"])
if __name__=="__main__":unittest.main()

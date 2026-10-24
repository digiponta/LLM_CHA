import tempfile
import unittest
from pathlib import Path
from unapproved_llm_intake_v074446 import _save
from unapproved_semantic_search_v0801 import search_semantic

def candidate(id,semantic,original="量子ビットは量子情報の基本単位である。",state="UNAPPROVED"):
    return {"id":id,"subject":"量子ビット","natural_language":original,
            "source":"https://ja.wikipedia.org/wiki/量子ビット",
            "state":state,"truth_state":"EXTERNAL_UNVERIFIED",
            "semantic_candidate":semantic,"train_ready":False}

class StructuredSearchTests(unittest.TestCase):
    def test_structured_found(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"store.json"
            _save(p,{"candidates":[candidate("a",{"status":"STRUCTURED","subject":"量子ビット","relation":"is_basic_unit","object":"基本単位"})]})
            result=search_semantic("量子ビットとは",p)
            self.assertEqual(result["status"],"FOUND")
            self.assertEqual(result["relation"],"is_basic_unit")
            self.assertFalse(result["model_generated"])
            self.assertFalse(result["train_ready"])
    def test_unstructured_not_eligible(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"store.json"
            _save(p,{"candidates":[candidate("a",{"status":"UNSTRUCTURED"})]})
            self.assertEqual(search_semantic("量子ビットとは",p)["status"],"NO_STRUCTURED_MATCH")
    def test_conflicting_and_deictic_not_eligible(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"store.json"
            semantic={"status":"STRUCTURED","subject":"量子ビット","relation":"is_basic_unit","object":"基本単位"}
            _save(p,{"candidates":[candidate("a",semantic,state="REVIEW_CONFLICT"),
                                   candidate("b",semantic,original="それに対して量子ビットは基本単位である。")]})
            self.assertEqual(search_semantic("量子ビットとは",p)["status"],"NO_STRUCTURED_MATCH")
    def test_not_a_model(self):
        self.assertEqual(search_semantic("")["status"],"INVALID_QUESTION")
if __name__=="__main__":unittest.main()

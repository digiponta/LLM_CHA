import tempfile
import unittest
from pathlib import Path
from unapproved_llm_intake_v074446 import _save
from unapproved_llm_compare_v074447 import requires_context,unapproved_answer

def item(id,text):
    return {"id":id,"subject":"量子ビット","natural_language":text,
            "source":"https://ja.wikipedia.org/wiki/量子ビット",
            "state":"UNAPPROVED","truth_state":"EXTERNAL_UNVERIFIED"}

class StandaloneEvidenceTests(unittest.TestCase):
    def test_pronoun_prefix_rejected(self):
        self.assertTrue(requires_context("それに対して量子ビットは重ね合わせを持つ。"))
        self.assertTrue(requires_context("そのような状態が可能である。"))
        self.assertFalse(requires_context("量子ビットは量子情報の基本単位である。"))
    def test_standalone_preferred(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"u.json"
            _save(path,{"version":"v0.7.44.46","candidates":[
                item("a","それに対して量子ビットは重ね合わせを持つ。"),
                item("b","量子ビットは量子情報の基本単位である。")]})
            result=unapproved_answer("量子ビットとは",path)
            self.assertEqual(result["candidate_id"],"b")
    def test_only_dependent_text_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"u.json"
            _save(path,{"version":"v0.7.44.46","candidates":[
                item("a","それに対して量子ビットは重ね合わせを持つ。")]})
            self.assertEqual(unapproved_answer("量子ビットとは",path)["status"],"NO_STANDALONE_EVIDENCE")

if __name__=="__main__":unittest.main()

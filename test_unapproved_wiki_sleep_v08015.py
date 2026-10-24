import tempfile
import unittest
from pathlib import Path
from unapproved_llm_intake_v074446 import _save
from unapproved_wiki_sleep_v08015 import eligible_candidates,sleep_unapproved_wikipedia

def make_row(cid, status="STRUCTURED",state="UNAPPROVED"):
    return {"id":cid,"subject":"量子ビット","natural_language":"量子ビットは基本単位である。",
      "source":"https://ja.wikipedia.org/wiki/量子ビット","source_type":"Wikipedia",
      "truth_state":"EXTERNAL_UNVERIFIED","state":state,
      "semantic_candidate":{"status":status,"subject":"量子ビット",
                            "relation":"is_basic_unit","object":"基本単位"}}

class WikiSleepTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.store=self.root/"store.json"
    def test_select_only_eligible(self):
        _save(self.store,{"candidates":[make_row("one"),make_row("two","UNSTRUCTURED"),
                         make_row("three",state="REVIEW_CONFLICT")]})
        self.assertEqual([r["id"] for r in eligible_candidates(self.store)],["one"])
    def test_no_pending_no_training(self):
        _save(self.store,{"candidates":[]})
        out=sleep_unapproved_wikipedia(store=self.store)
        self.assertEqual(out["status"],"NO_ELIGIBLE")
    def test_injectable_training_and_isolation_contract(self):
        _save(self.store,{"candidates":[make_row("one")]})
        observed=[]
        def trainer(rows,base,tokenizer,destination,rank,epochs,lr):
            observed.append([r["id"] for r in rows])
            return {"candidate_count":len(rows)}
        result=sleep_unapproved_wikipedia(
            store=self.store,base=self.root/"base.pt",
            tokenizer_path=self.root/"tokenizer.json",
            output_dir=self.root/"output",trainer=trainer)
        self.assertEqual(result["status"],"TRAINED")
        self.assertEqual(observed,[["one"]])
        self.assertFalse(result["trusted_changed"])
        self.assertFalse(result["approved"])
    def test_sleep_is_wired(self):
        text=Path(__file__).with_name("chat.py").read_text(encoding="utf-8")
        self.assertIn("from unapproved_wiki_sleep_v08015 import sleep_unapproved_wikipedia",text)
        self.assertIn("[unapproved wiki sleep: status=",text)

if __name__=="__main__":unittest.main()

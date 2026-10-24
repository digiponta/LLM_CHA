import json
import tempfile
import unittest
from pathlib import Path
from unapproved_llm_intake_v074446 import _save
from prepare_holdout_v08023 import prepare

class HoldoutPreparationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.dir=Path(self.temp.name)
        self.store=self.dir/"train.json"
        self.input=self.dir/"curated.json"
        self.dest=self.dir/"holdout.json"
        _save(self.store,{"candidates":[{"id":"trained-01",
            "subject":"量子ビット","natural_language":"量子ビットは量子情報の基本単位である。"}]})
    def data(self,kind="UNSEEN_FACT",count=5):
        return {"independent_source_attested":True,
          "records":[{"id":"independent-"+str(i),
            "evaluation_kind":kind,"question":"新規科学テーマ"+str(i)+"の定義は？",
            "reference_answer":"独立資料に基づく検証用記述"+str(i)+"。",
            "source_url":"https://source.test/article/"+str(i),
            "source_excerpt":"独立資料に基づく検証用記述"+str(i)+"。"} for i in range(count)]}
    def store_data(self,data):
        self.input.write_text(json.dumps(data,ensure_ascii=False),encoding="utf-8")
    def test_dry_run_does_not_write(self):
        self.store_data(self.data())
        result=prepare(self.input,self.store,self.dest)
        self.assertEqual(result["status"],"READY_FOR_REVIEW")
        self.assertFalse(self.dest.exists())
    def test_write_and_no_overwrite(self):
        self.store_data(self.data())
        first=prepare(self.input,self.store,self.dest,write=True)
        self.assertEqual(first["status"],"STAGED")
        self.assertEqual(prepare(self.input,self.store,self.dest,write=True)["status"],"OUTPUT_EXISTS")
    def test_reject_placeholder(self):
        data=self.data()
        data["records"][0]["id"]="replace-with-independent-id"
        self.store_data(data)
        self.assertEqual(prepare(self.input,self.store,self.dest)["status"],"NOT_READY")
    def test_reject_paraphrase_in_formal_holdout(self):
        self.store_data(self.data(kind="PARAPHRASE"))
        self.assertEqual(prepare(self.input,self.store,self.dest)["status"],"REVIEW_REQUIRED")
    def test_reject_inadequate_size(self):
        self.store_data(self.data(count=1))
        self.assertEqual(prepare(self.input,self.store,self.dest)["status"],"NOT_READY")
if __name__=="__main__":unittest.main()

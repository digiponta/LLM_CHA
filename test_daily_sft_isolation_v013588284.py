import json,tempfile,unittest
from pathlib import Path
from check_daily_sft_isolation_v013588284 import check

class DailySftIsolationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();d=Path(self.tmp.name)
        self.train=d/"train.jsonl";self.holdout=d/"holdout.json"
        self.holdout.write_text(json.dumps({"cases":[{"question":"今日は何をしてる？","example_acceptable":"今は会話中だよ。"}]},ensure_ascii=False),encoding="utf-8")
    def tearDown(self):self.tmp.cleanup()
    def write(self,*rows):
        self.train.write_text("\n".join(json.dumps(r,ensure_ascii=False) for r in rows)+"\n",encoding="utf-8")
    def test_separate_training_pair(self):
        self.write({"user":"おはよう","assistant":"おはよう。","source":"chat-manual"})
        x=check(self.train,self.holdout)
        self.assertEqual(x["status"],"PASS")
        self.assertFalse(x["semantic_independence_verified"])
    def test_question_leakage(self):
        self.write({"user":"今日は何をしてる？","assistant":"こんにちは","source":"chat-manual"})
        self.assertEqual(check(self.train,self.holdout)["status"],"BLOCKED")
    def test_answer_leakage(self):
        self.write({"user":"おはよう","assistant":"今は会話中だよ。","source":"chat-manual"})
        self.assertEqual(check(self.train,self.holdout)["status"],"BLOCKED")
    def test_duplicate(self):
        row={"user":"こんにちは","assistant":"やあ","source":"chat-manual"}
        self.write(row,row)
        self.assertIn([2,"DUPLICATE_PROMPT"],check(self.train,self.holdout)["issues"])
    def test_untrusted_source(self):
        self.write({"user":"おはよう","assistant":"やあ","source":"chat-auto"})
        self.assertEqual(check(self.train,self.holdout)["status"],"BLOCKED")
if __name__=="__main__":unittest.main()

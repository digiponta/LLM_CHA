import json,tempfile,unittest
from pathlib import Path
from prepare_generalization_v0212 import prepare,clean,row_topic

class GeneralizationTests(unittest.TestCase):
    def test_topic_filter(self):
        self.assertEqual(row_topic({"user":"人: 写真を撮っています","assistant":"夜景が好きです"}),{"photo"})
        self.assertEqual(row_topic({"user":"人: 小説です","assistant":"何のジャンルですか？"}),set())
    def test_clean(self):
        self.assertFalse(clean({"user":"人: SFです","assistant":"そうですね"}))
        self.assertTrue(clean({"user":"人: SFです","assistant":"宇宙探査の物語が好きです。"}))
    def test_distinct_splits_and_topic_holdout(self):
        with tempfile.TemporaryDirectory() as d:
            src=Path(d)/"src";src.mkdir();dst=Path(d)/"out"
            rows={
              "train":[{"user":"人: 写真を撮っています","assistant":"夜景の撮影が好きです。"},
                       {"user":"人: 読書をしています","assistant":"どんなジャンルの本が好きですか？"}],
              "val":[{"user":"人: 写真が好きです","assistant":"どんな写真を撮りますか？"},
                     {"user":"人: 散歩が好きです","assistant":"どの道をよく歩きますか？"}],
              "test":[{"user":"人: 音楽が好きです","assistant":"どんな音楽をよく聴きますか？"}]}
            for name,values in rows.items():
                (src/f"rpc_multiturn_{name}.jsonl").write_text(
                    "".join(json.dumps(r,ensure_ascii=False)+"\n" for r in values),encoding="utf-8")
            result=prepare(src,dst,max_train=100)
            self.assertEqual(result["counts"]["train"],1)
            self.assertEqual(result["counts"]["topic_holdout"],1)
            train=(dst/"train.jsonl").read_text(encoding="utf-8")
            self.assertNotIn("写真",train)
            self.assertIn("写真",(dst/"topic_holdout.jsonl").read_text(encoding="utf-8"))
            self.assertTrue((dst/"test.jsonl").is_file())
if __name__=="__main__":unittest.main()

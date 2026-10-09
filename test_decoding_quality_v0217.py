import csv,json,tempfile,unittest
from pathlib import Path
from evaluate_decoding_quality_v0217 import blind_records,build,score

class DecodingQualityTests(unittest.TestCase):
    def setUp(self):
        self.data={"models":{"m":{"greedy":{"records":[{"prompt":"人: SFです","reference":"SFなら宇宙探査の話ですね","generated":"そう。","tokens":3,"terminated_by_eos":True}]},
            "sampling_t07":{"records":[{"prompt":"人: SFです","reference":"SFなら宇宙探査の話ですね","generated":"SFなら宇宙探査が面白い。","tokens":12,"terminated_by_eos":True}]}}}}
    def test_blind_sheet_and_key(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d);(path/"in.json").write_text(json.dumps(self.data,ensure_ascii=False),encoding="utf-8")
            self.assertEqual(build(path/"in.json",path/"out"),2)
            rows=list(csv.DictReader((path/"out"/"blind_ratings.csv").open(encoding="utf-8-sig",newline="")))
            self.assertEqual(len(rows),2)
            self.assertNotIn("model",rows[0])
            self.assertNotIn("method",rows[0])
    def test_empty_ratings(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d);(path/"in.json").write_text(json.dumps(self.data),encoding="utf-8")
            build(path/"in.json",path/"out")
            self.assertEqual(score(path/"out"/"blind_ratings.csv",path/"out"/"blind_key.json"),{})
if __name__=="__main__":unittest.main()

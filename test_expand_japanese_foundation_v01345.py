import json,tempfile,unittest
from pathlib import Path
from expand_japanese_foundation_v01345 import split_sentences,expand
class ExpansionTests(unittest.TestCase):
    def test_split(self):
        text="最初の文章では、日々の出来事を静かに振り返った。次の文章では、研究の進め方について丁寧に説明した。"
        rows,_=split_sentences(text)
        self.assertEqual(len(rows),2)
    def test_dedup(self):
        s="研究者は計測機器の応答を調べ、温度の変化と測定値の関係を確認した。"
        rows,_=split_sentences(s+"\n"+s)
        self.assertEqual(len(rows),1)
    def test_escape(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/"manifest.json").write_text(json.dumps({"sources":[{"id":"a","path":"../other.txt","license":"owned","provenance":"test","approved_for_training":True},{"id":"b","path":"missing.txt","license":"owned","provenance":"test","approved_for_training":True}]}),encoding="utf8")
            with self.assertRaises(ValueError):expand(p/"manifest.json",p/"out")
    def test_round_trip(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            sentence1="庭にある小さな木は雨上がりに葉を広げ、朝の光を受けて静かに輝いていた。"
            sentence2="実験の手順を変更した担当者は測定結果を記録し、前の条件と比較して差を調べた。"
            (p/"a.txt").write_text(sentence1+"\n",encoding="utf8")
            (p/"b.txt").write_text(sentence2+"\n",encoding="utf8")
            rows=[{"id":k,"path":k+".txt","license":"owned","provenance":"local",
                   "approved_for_training":True} for k in ("a","b")]
            (p/"manifest.json").write_text(json.dumps({"sources":rows}),encoding="utf8")
            audit=expand(p/"manifest.json",p/"output")
            self.assertEqual(audit["counts"],{"train":1,"val":1})
            self.assertTrue((p/"output"/"audit.json").exists())
    def test_requires_approval(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            row={"id":"a","path":"a.txt","license":"unknown","provenance":"test","approved_for_training":False}
            (p/"manifest.json").write_text(json.dumps({"sources":[row]}),encoding="utf8")
            with self.assertRaises(ValueError):expand(p/"manifest.json",p/"out")
if __name__=="__main__":unittest.main()

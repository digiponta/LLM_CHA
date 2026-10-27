import tempfile,unittest
from pathlib import Path
from normalize_aozora_foundation_v01347 import strip_aozora,extract_sentences,convert
class AozoraTests(unittest.TestCase):
    def test_ruby(self):
        s,stats=strip_aozora("｜銀河《ぎんが》の星は夜の空を明るく照らし、旅人は遠い山まで歩いていった。")
        self.assertIn("銀河の星",s)
        self.assertNotIn("《",s)
        self.assertEqual(stats["ruby_removed"],1)
    def test_annotation(self):
        s,stats=strip_aozora("遠くに見える建物には［＃「建物」に傍点］昔の人の暮らしが残されていた。")
        self.assertNotIn("［＃",s)
        self.assertEqual(stats["annotations_removed"],1)
    def test_sentence_split(self):
        ss=extract_sentences("研究者は観測の記録を調べ、現象の違いを慎重に比較した。新しい実験では気温の変化も同時に記録した。")
        self.assertEqual(len(ss),2)
    def test_convert_requires_manual_review(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);src=p/"in.txt"
            src.write_text("庭の花が咲き始めたので、友人と一緒に写真を撮りながら散歩した。\n",encoding="utf8")
            result=convert(src,p/"out.txt",p/"audit.json")
            self.assertFalse(result["training_approved"])
            self.assertTrue((p/"out.txt").exists())
    def test_do_not_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);src=p/"a.txt";out=p/"out.txt"
            src.write_text("庭の花が咲き始めたので、友人と一緒に写真を撮りながら散歩した。",encoding="utf8")
            out.write_text("EXISTING",encoding="utf8")
            with self.assertRaises(FileExistsError):convert(src,out,p/"report.json")
if __name__=="__main__":unittest.main()

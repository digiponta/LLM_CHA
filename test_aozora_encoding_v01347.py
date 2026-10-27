"""v0.13.47 CP932 regression: uploaded Aozora-style text may use Shift-JIS."""
import tempfile,unittest
from pathlib import Path
from normalize_aozora_foundation_v01347 import convert,read_japanese_source
class EncodingTests(unittest.TestCase):
    def test_cp932_detect_and_convert(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);source=p/"aozora.txt"
            sentence="吾輩は猫である。名前はまだ無い。これは古い文学の文章を利用して変換処理を確認する例文である。"
            source.write_bytes(sentence.encode("cp932"))
            text,enc=read_japanese_source(source)
            self.assertEqual(enc,"cp932")
            self.assertIn("吾輩",text)
            report=convert(source,p/"out.txt",p/"report.json")
            self.assertEqual(report["encoding"],"cp932")
            self.assertGreater(report["sentences"],0)
    def test_utf8_detect(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"x.txt";p.write_text("日本語の文章です。",encoding="utf-8")
            self.assertEqual(read_japanese_source(p)[1],"utf-8-sig")
if __name__=="__main__":unittest.main()

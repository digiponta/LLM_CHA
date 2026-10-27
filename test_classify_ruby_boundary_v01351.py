import re,unittest
from classify_ruby_boundary_v01351 import CANDIDATE,inspect_match,classify_lines
READINGS={"見当":"けんとう","掌":"てのひら","獰悪":"どうあく","大":"おお"}
class BoundaryTests(unittest.TestCase):
    def check(self,text,word,reading,following):
        m=CANDIDATE.search(text);self.assertIsNotNone(m)
        result=inspect_match(m,READINGS)
        self.assertEqual(result["label"],"RUBY_CANDIDATE")
        self.assertEqual((result["kanji"],result["reading"],result["following"]),(word,reading,following))
    def test_particle_after_reading(self):
        self.check("見当けんとうがつかぬ","見当","けんとう","がつかぬ")
    def test_reading_then_na(self):
        self.check("獰悪どうあくな","獰悪","どうあく","な")
    def test_palmar(self):
        self.check("掌てのひらに","掌","てのひら","に")
    def test_ambiguous_okurigana(self):
        r=inspect_match(CANDIDATE.search("見ると"),READINGS)
        self.assertEqual(r["label"],"AMBIGUOUS")
    def test_readonly(self):
        src=["見当けんとうがつかぬ。","見ると云って帰った。"]
        backup=list(src);report=classify_lines(src,READINGS)
        self.assertEqual(src,backup)
        self.assertEqual(report["automatic_replacements"],0)
        self.assertFalse(report["training_approved"])
if __name__=="__main__":unittest.main()

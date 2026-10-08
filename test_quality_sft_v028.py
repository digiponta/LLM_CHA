import json,tempfile,unittest
from pathlib import Path
from prepare_quality_sft_v028 import generic,valid,transform

class QualitySFTTests(unittest.TestCase):
    def test_filter(self):
        self.assertTrue(generic("そうですね。"))
        self.assertFalse(valid({"user":"人: SFです","assistant":"そうですね"}))
        self.assertTrue(valid({"user":"人: SFです","assistant":"SF小説には宇宙探査を描く作品があります。"}))
    def test_preformatted_anchors_and_validation_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            train=root/"train.jsonl";anchor=root/"anchors.jsonl";val=root/"val.jsonl"
            rows=[{"user":"人: SFです","assistant":"そうですね"},
                  {"user":"人: SFです","assistant":"SF小説では未来社会や宇宙探査が扱われます。"}]
            train.write_text("".join(json.dumps(r,ensure_ascii=False)+"\n" for r in rows),encoding="utf-8")
            anchor.write_text(json.dumps({"user":"あなたは誰ですか","assistant":"長門有希。"},ensure_ascii=False)+"\n",encoding="utf-8")
            val.write_text("untouched",encoding="utf-8")
            result=transform(train,anchor,root/"out",max_train=10)
            self.assertEqual(result["selected_rows"],1)
            saved=json.loads((root/"out"/"persona_anchors_preformatted.jsonl").read_text(encoding="utf-8"))
            self.assertEqual(saved["user"],"人: あなたは誰ですか")
            self.assertEqual(val.read_text(encoding="utf-8"),"untouched")
if __name__=="__main__":unittest.main()

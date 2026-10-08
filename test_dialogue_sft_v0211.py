import json,tempfile,unittest
from pathlib import Path
from prepare_dialogue_sft_v0211 import TRAIN,HOLDOUT,expand,build

class DialogueSFTTests(unittest.TestCase):
    def test_context_is_training_prompt(self):
        rows=expand(TRAIN[:1])
        self.assertEqual(rows[0]["user"],"人: 最近、小説にはまっています")
        self.assertIn("AI: どんなジャンルを読んでいるの？",rows[1]["user"])
        self.assertIn("人: SFです",rows[1]["user"])
    def test_topic_disjoint(self):
        a=expand(TRAIN);b=expand(HOLDOUT)
        self.assertFalse({r["user"] for r in a}&{r["user"] for r in b})
    def test_dataset_writes(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);q=root/"quality.jsonl";p=root/"persona.jsonl"
            q.write_text(json.dumps({"user":"人: 読書","assistant":"どんな本が好きですか？"},ensure_ascii=False)+"\n",encoding="utf-8")
            p.write_text(json.dumps({"user":"人: あなたは誰ですか","assistant":"長門有希。"},ensure_ascii=False)+"\n",encoding="utf-8")
            result=build(root/"out",q,p,background_limit=1)
            self.assertEqual(result["heldout_rows"],len(expand(HOLDOUT)))
            self.assertTrue((root/"out"/"dialogue_train.jsonl").exists())
            self.assertTrue((root/"out"/"dialogue_val.jsonl").exists())
if __name__=="__main__":unittest.main()

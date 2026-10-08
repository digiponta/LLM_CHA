import json
from pathlib import Path
import tempfile
import unittest
from prepare_realpersonachat_v020 import convert, split_for, dialogue_pairs

class RPCTests(unittest.TestCase):
    def sample(self, n):
        return {"dialogue_id": n, "utterances": [
            {"interlocutor_id":"A","text":"こんにちは"},
            {"interlocutor_id":"B","text":"こんにちは！"},
            {"interlocutor_id":"A","text":"今日は元気？"},
            {"interlocutor_id":"B","text":"元気です。"},
        ]}

    def test_examples(self):
        pairs = list(dialogue_pairs(self.sample(1)))
        self.assertEqual(len(pairs), 3)
        self.assertEqual(pairs[0]["assistant"], "こんにちは！")

    def test_group_split_deterministic(self):
        self.assertEqual(split_for("123"), split_for("123"))
        self.assertIn(split_for("123"), ("train", "val", "test"))

    def test_mask_excluded(self):
        row = self.sample(1)
        row["utterances"][1]["text"] = "＊＊"
        self.assertFalse(any(pair["assistant"] == "＊＊" for pair in dialogue_pairs(row)))

    def test_conversion(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            src, dst = base/"dialogues", base/"out"
            src.mkdir()
            for i in range(1, 51):
                (src / f"{i:05}.json").write_text(json.dumps(self.sample(i),ensure_ascii=False),encoding="utf-8")
            report = convert(src,dst)
            self.assertEqual(sum(report["dialogues"].values()), 50)
            self.assertGreater(sum(report["pairs"].values()), 0)
            for split in ("train","val","test"):
                self.assertTrue((dst/f"rpc_{split}.jsonl").exists())
            self.assertEqual(len(json.loads((dst/"rpc_manifest.json").read_text(encoding="utf-8"))["pairs"]),3)

if __name__=="__main__":
    unittest.main()

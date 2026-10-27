import json,tempfile,unittest
from pathlib import Path
from train_rpc_dialogue_sft_v01334 import read_rows,verify_disjoint

def item(did):
    return {"user":"相手: こんにちは","assistant":"よろしくお願いします",
            "source":"rpc-dialogue-sft","approval_state":"UNAPPROVED",
            "dialogue_id":did}

class TestRPCTraining(unittest.TestCase):
    def test_read_rows(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"train.jsonl"
            path.write_text("\n".join(json.dumps(item(i),ensure_ascii=False) for i in range(3))+"\n",encoding="utf-8")
            self.assertEqual(len(read_rows(path,2)),2)
    def test_split_nonoverlap(self):
        self.assertEqual(verify_disjoint([item(1)],[item(2)],[item(3)]),[1,1,1])
    def test_split_overlap_rejected(self):
        with self.assertRaises(ValueError):
            verify_disjoint([item(1)],[item(1)],[item(3)])
    def test_unapproved_required(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"train.jsonl"
            row=item(1);row["approval_state"]="APPROVED"
            path.write_text(json.dumps(row,ensure_ascii=False)+"\n",encoding="utf-8")
            with self.assertRaises(ValueError):read_rows(path)

if __name__=="__main__":unittest.main()

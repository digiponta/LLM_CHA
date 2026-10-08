import json
from pathlib import Path
import tempfile
import unittest
from prepare_conversation_replay_v021 import build, DEFAULT_ANCHORS

class ReplayTests(unittest.TestCase):
    def test_split_and_anchor_separation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root/"rpc.jsonl"
            source.write_text("".join(json.dumps({"user":f"Q{i}","assistant":f"A{i}"},ensure_ascii=False)+"\n" for i in range(30)),encoding="utf-8")
            output=root/"prepared"
            report=build(source,output,20,7,42)
            train=[json.loads(line) for line in (output/"rpc_replay_train.jsonl").read_text(encoding="utf-8").splitlines()]
            anchor=[json.loads(line) for line in (output/"rpc_replay_anchors.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(train),20)
            self.assertEqual(len(anchor),len(DEFAULT_ANCHORS))
            self.assertEqual(report["effective_anchor_rows"],7*len(DEFAULT_ANCHORS))
            self.assertEqual(len((output/"rpc_replay_anchor_eval.jsonl").read_text(encoding="utf-8").splitlines()),len(DEFAULT_ANCHORS))
    def test_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); source=root/"rpc.jsonl"
            source.write_text("".join(json.dumps({"user":str(i),"assistant":"a"})+"\n" for i in range(50)),encoding="utf-8")
            build(source,root/"a",10,2,42);build(source,root/"b",10,2,42)
            self.assertEqual((root/"a"/"rpc_replay_train.jsonl").read_bytes(),(root/"b"/"rpc_replay_train.jsonl").read_bytes())
if __name__=="__main__":unittest.main()

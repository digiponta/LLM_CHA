import tempfile
import json
import unittest
from pathlib import Path
from prepare_rpc_dialogue_sft_v01333 import validate_dialogue,extract,split_id,prepare

SAMPLE={"dialogue_id":1,"interlocutors":["AA","AB"],"utterances":[
    {"utterance_id":0,"interlocutor_id":"AA","text":"よろしくお願いします"},
    {"utterance_id":1,"interlocutor_id":"AB","text":"こちらこそ"},
    {"utterance_id":2,"interlocutor_id":"AA","text":"涼しいですね"},
    {"utterance_id":3,"interlocutor_id":"AB","text":"そうですね"}]}

class RPCTests(unittest.TestCase):
    def test_validate(self):
        did,records=validate_dialogue(SAMPLE)
        self.assertEqual(did,1)
        self.assertEqual(len(records),4)
    def test_pairs(self):
        rows=extract(SAMPLE)
        self.assertEqual(len(rows),3)
        self.assertEqual(rows[0]["assistant"],"こちらこそ")
        self.assertIn("相手: よろしく",rows[0]["user"])
        self.assertEqual(rows[2]["approval_state"],"UNAPPROVED")
    def test_stable_split(self):
        self.assertEqual(split_id(42),split_id(42))
    def test_no_duplicate_utterance(self):
        bad=json.loads(json.dumps(SAMPLE))
        bad["utterances"][1]["utterance_id"]=0
        with self.assertRaises(ValueError):validate_dialogue(bad)
    def test_prepare_and_grouping(self):
        with tempfile.TemporaryDirectory() as tmp:
            src=Path(tmp)/"src";out=Path(tmp)/"out";src.mkdir()
            (src/"00001.json").write_text(json.dumps(SAMPLE),encoding="utf-8")
            report=prepare(src,out)
            self.assertEqual(sum(report["counts"].get(s+"_pairs",0) for s in ("train","val","test")),3)
            self.assertTrue((out/"rpc_sft_manifest_v01333.json").exists())
            with self.assertRaises(FileExistsError):prepare(src,out)

if __name__=="__main__":unittest.main()

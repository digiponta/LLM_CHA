import ast
import json
import tempfile
import unittest
from pathlib import Path
from multi_topic_evidence_v0639 import TopicEvidenceContext
from persistent_topic_context_v0640 import SCHEMA,save_context,load_context

class PersistenceTests(unittest.TestCase):
    def test_roundtrip_and_restore(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"session.json"
            x=TopicEvidenceContext()
            x.remember("スターバックス","","wiki-starbucks")
            x.remember("トヨタ","本社は豊田市","wiki-toyota")
            x.restore("スターバックスに戻って")
            save_context(x,p)
            y=load_context(p)
            self.assertEqual(y.active,"スターバックス")
            self.assertEqual(y.items["トヨタ"]["extract"],"本社は豊田市")
            self.assertEqual(y.items["トヨタ"]["truth_state"],"EXTERNAL_UNVERIFIED")
    def test_corrupted_state_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"bad.json"
            p.write_text('{"schema":"old","active":null,"topics":[]}',encoding="utf-8")
            with self.assertRaises(ValueError):load_context(p)
    def test_forged_approved_state_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"bad.json"
            p.write_text(json.dumps({"schema":SCHEMA,"active":"A","topics":[{"topic":"A","extract":"","source":"",
                "truth_state":"APPROVED"}]}),encoding="utf-8")
            with self.assertRaises(ValueError):load_context(p)
    def test_missing_active_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"bad.json"
            p.write_text(json.dumps({"schema":SCHEMA,"active":"missing","topics":[]}),encoding="utf-8")
            with self.assertRaises(ValueError):load_context(p)
    def test_over_capacity_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"bad.json"
            rows=[{"topic":str(i),"extract":"","source":"","truth_state":"EXTERNAL_UNVERIFIED"} for i in range(5)]
            p.write_text(json.dumps({"schema":SCHEMA,"active":None,"topics":rows}),encoding="utf-8")
            with self.assertRaises(ValueError):load_context(p)
    def test_chat_wiring(self):
        source=Path("chat.py").read_text(encoding="utf-8")
        ast.parse(source)
        for command in ("/context-save","/context-load","/context-clear"):
            self.assertIn(command,source)
if __name__=="__main__":unittest.main()

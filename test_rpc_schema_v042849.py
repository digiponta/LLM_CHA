import json
import tempfile
import unittest
from pathlib import Path
from inspect_rpc_schema_v042849 import inspect_file

class SchemaTests(unittest.TestCase):
    def run_rows(self, rows):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/"rpc.jsonl"
            p.write_text("\n".join(json.dumps(r,ensure_ascii=False) for r in rows)+"\n",encoding="utf-8")
            return inspect_file(p)
    def test_object_keys(self):
        report=self.run_rows([{"id":"abc","turns":[{"role":"user","text":"SECRET"}]}])
        self.assertEqual(report["field_counts"]["turns"],1)
        self.assertNotIn("SECRET",json.dumps(report))
        self.assertNotIn('"abc"',json.dumps(report))
    def test_missing_id(self):
        self.assertEqual(self.run_rows([{"question":"Q","answer":"A"}])["no_identified_id"],1)
    def test_repeated_turn_id(self):
        r=self.run_rows([{"dialogue_id":"a","turn":0},{"dialogue_id":"a","turn":1}])
        self.assertEqual(r["duplicate_id_values_in_sample"],1)
    def test_integer_id(self):
        r=self.run_rows([{"id":12,"turns":[]}])
        self.assertEqual(r["id_field_types"]["id:int"],1)
    def test_non_object(self):
        self.assertEqual(self.run_rows([["a"]])["nonobject_types"]["list"],1)
    def test_limit(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/"rpc.jsonl"
            p.write_text('{"id":"1"}\n{"id":"2"}\n',encoding="utf-8")
            self.assertEqual(inspect_file(p,1)["records_examined"],1)
    def test_invalid_limit(self):
        with self.assertRaises(ValueError):
            inspect_file("unused",0)
if __name__=="__main__":
    unittest.main()

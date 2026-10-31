import json,tempfile,unittest
from pathlib import Path
from inspect_real_persona_schema_v013588291 import inspect
class TestSchema(unittest.TestCase):
    def test_missing(self):
        with tempfile.TemporaryDirectory() as d:self.assertEqual(inspect(d)["status"],"DIALOGUES_NOT_FOUND")
    def test_structure_no_text(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"real_persona_chat"/"dialogues";p.mkdir(parents=True)
            (p/"1.json").write_text(json.dumps({"utterances":[{"speaker":"A","text":"PRIVATE_SENTENCE"}],"interlocutors":["A","B"],"evaluations":{}}))
            x=inspect(d)
            self.assertEqual(x["file_count"],1)
            self.assertNotIn("PRIVATE_SENTENCE",json.dumps(x))
            self.assertEqual(x["samples"][0]["utterances"]["first"]["keys"],["speaker","text"])
if __name__=="__main__":unittest.main()

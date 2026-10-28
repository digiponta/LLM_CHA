import json,tempfile,unittest
from pathlib import Path
from dialogue_format_v0135817 import dialogue_for,prompt_for,split_dialogue,canonicalize_legacy,check_prompt
from audit_offline_replay_v0135810 import read_file

class DialogueFormatAlignmentTests(unittest.TestCase):
    def test_prompt_equals_training_prefix(self):
        line=dialogue_for("こんにちは。","こんにちは。")
        prefix,answer=split_dialogue(line)
        self.assertEqual(prefix,prompt_for("こんにちは。"))
        self.assertTrue(check_prompt(line,prefix))
        self.assertEqual(answer,"こんにちは。")
    def test_legacy_normalization(self):
        self.assertEqual(canonicalize_legacy("人: 質問 AI: 回答"),dialogue_for("質問","回答"))
    def test_no_ambiguous_multiturn_silent_conversion(self):
        with self.assertRaises(ValueError):
            canonicalize_legacy("人: 質問\nAI: 回答\n人: 続き\nAI: ")
    def test_invalid_empty(self):
        with self.assertRaises(ValueError):prompt_for(" ")
        with self.assertRaises(ValueError):dialogue_for("質問"," ")
    def test_approved_jsonl_uses_same_prompt(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/"sample.jsonl"
            f.write_text(json.dumps({"approved":True,"user":"質問","assistant":"回答"},ensure_ascii=False),encoding="utf8")
            line=read_file(f)[0]
            self.assertEqual(split_dialogue(line)[0],prompt_for("質問"))
    def test_legacy_text_is_not_auto_approved_or_rewritten(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/"sample.txt"
            f.write_text("人: 質問 AI: 回答\n",encoding="utf8")
            self.assertEqual(read_file(f),["人: 質問 AI: 回答"])
if __name__=="__main__":unittest.main()

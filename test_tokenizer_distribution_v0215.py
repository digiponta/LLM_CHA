import unittest, tempfile, json
from pathlib import Path
from diagnose_tokenizer_distribution_v0215 import norm
from diagnose_generic_amplification_v0215 import compare

class TokenizerAuditTests(unittest.TestCase):
    def test_normalize(self):
        self.assertEqual(norm("そうですね。"),"そうですね")
    def test_reference_matching_required(self):
        class T:pass
        with tempfile.TemporaryDirectory() as directory:
            file=Path(directory)/"ref.jsonl"
            file.write_text(json.dumps({"user":"人: elsewhere","assistant":"こんにちは"})+"\n",encoding="utf-8")
            with self.assertRaises(ValueError):
                compare({"m":{"samples":[{"prompt":"人: not found","generated":"そう。"}]}},str(file),T())
if __name__=="__main__":unittest.main()

import unittest,tempfile,json
from pathlib import Path
from unittest.mock import Mock
from evaluate_semantic_expansion_transfer_v02329 import evaluation_cases,prompts,compare
from evaluate_semantic_transfer_v02327 import PROBES
class ThreeModelTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=Path(self.tmp.name)/"expand.jsonl"
        self.path.write_text(json.dumps({"variant_type":"original","review_status":"APPROVED",
            "prompt":"話題: LLM\n目的: 学習\n人: LLMを勉強したい\nAI: ",
            "canonical":{"topic":"LLM","purposes":["learning"]},"answer":"LLMの基礎を学ぶ。"},
            ensure_ascii=False)+"\n",encoding="utf-8")
    def tearDown(self):self.tmp.cleanup()
    def test_cases(self):
        c=evaluation_cases(self.path)
        self.assertEqual(len(c),1+len(PROBES)+6)
        self.assertEqual(set(prompts(c[0])),{"raw","short"})
        self.assertEqual(set(prompts(c[-1])),{"raw"})
    def test_mock_consistent_decode(self):
        model={}
        for k in ("base","original","expanded"):
            model[k]=Mock()
            model[k].generate.return_value={"text":k,"generated_tokens":1,"elapsed_seconds":0.1}
        cases=evaluation_cases(self.path)[:1]
        x=compare(model,cases,max_new_tokens=13)
        self.assertEqual(len(x),1)
        for m in model.values():
            self.assertEqual(m.generate.call_count,2)
            self.assertTrue(all(c.kwargs["temperature"]==0 and c.kwargs["max_new_tokens"]==13 for c in m.generate.call_args_list))
    def test_holdout_contamination_rejected(self):
        probe=PROBES[0]
        from evaluate_semantic_transfer_v02327 import prompt_for
        row={"variant_type":"paraphrase","review_status":"APPROVED",
             "prompt":prompt_for({"kind":"unseen",**probe}),"canonical":{},"answer":"leak"}
        with self.path.open("a",encoding="utf-8") as f:f.write(json.dumps(row,ensure_ascii=False)+"\n")
        with self.assertRaisesRegex(ValueError,"contamination"):evaluation_cases(self.path)
if __name__=="__main__":unittest.main()

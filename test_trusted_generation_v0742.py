import unittest
from verify_trusted_generation_v0742 import make_probes,answer_match,summarize,perform

class FakeTokenizer:
    eos_id=99
    def encode(self,text,add_bos=False):
        self.last_prompt=text
        return [1,2,3]
    def decode(self,ids,skip_special_tokens=True):
        return "真空管は2/3乗特性。"

class FakeModel:
    def __init__(self):self.prompts=[]
    def generate(self,ids,**kwargs):
        self.prompts.append((list(ids),kwargs))
        return list(ids)+[5,99]

class TrustedGenerationTests(unittest.TestCase):
    def test_exact_pair_and_stability(self):
        probes=make_probes([{"id":"abc","user":"真空管の原文記述は",
                             "assistant":"真空管は2/3乗特性。"}])
        self.assertEqual(probes[0]["group"],"approved_exact")
        self.assertTrue(any(r["group"]=="stability" for r in probes))
    def test_generation_is_unassisted_and_greedy(self):
        model=FakeModel()
        tokenizer=FakeTokenizer()
        probes=[{"group":"approved_exact","question":"真空管の原文記述は",
                 "expected_answer":"真空管は2/3乗特性。","approved_id":"abc"}]
        result=perform(model,tokenizer,probes,32)
        self.assertTrue(result[0]["contains_expected_answer"])
        self.assertEqual(model.prompts[0][1]["temperature"],0.0)
        self.assertEqual(model.prompts[0][1]["repetition_penalty"],1.0)
        self.assertEqual(tokenizer.last_prompt,"人: 真空管の原文記述は\nAI: ")
    def test_empty_not_match(self):
        self.assertFalse(answer_match("hello",""))
    def test_summary_distinct_from_semantic_score(self):
        cases=[{"group":"approved_exact","contains_expected_answer":True,"term_hits":{}},
               {"group":"stability","contains_expected_answer":None,
                "term_hits":{"GPU":False}}]
        out=summarize(cases)
        self.assertEqual(out["approved_exact"]["answer_containment"],1)
        self.assertEqual(out["stability"]["term_all"],0)

if __name__=="__main__":unittest.main()

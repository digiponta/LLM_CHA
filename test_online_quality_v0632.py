import unittest
from evaluate_online_quality_v0632 import compare,score,load_cases

CASES=[
 {"id":"identity","group":"persona","prompt":"誰","expected_any":["長門有希"]},
 {"id":"existing","group":"known","prompt":"猫とは","expected_any":["猫"]},
 {"id":"added","group":"new","prompt":"合言葉","expected_any":["青"]},
]
class QualityGateTests(unittest.TestCase):
    def test_pass(self):
        r=compare({"identity":True,"existing":True,"added":False},
                  {"identity":True,"existing":True,"added":True},CASES,0,1)
        self.assertTrue(r["pass"])
        self.assertEqual(r["forgetting_rate"],0)
    def test_forgetting_blocks(self):
        r=compare({"identity":True,"existing":True,"added":False},
                  {"identity":False,"existing":True,"added":True},CASES,0,1)
        self.assertFalse(r["pass"])
        self.assertEqual(r["forgetting_rate"],0.5)
    def test_new_unknown_blocks(self):
        r=compare({"identity":True,"existing":True,"added":False},
                  {"identity":True,"existing":True,"added":False},CASES,0,1)
        self.assertFalse(r["pass"])
    def test_no_prior_correct_fails_closed(self):
        r=compare({"identity":False,"existing":False,"added":False},
                  {"identity":False,"existing":False,"added":True},CASES,0,1)
        self.assertFalse(r["pass"])
    def test_score(self):
        self.assertTrue(score("長門有希。",CASES[0]))
        self.assertFalse(score("誰かです",CASES[0]))
    def test_case_list_default(self):
        self.assertTrue(load_cases(None))
if __name__=="__main__":unittest.main()

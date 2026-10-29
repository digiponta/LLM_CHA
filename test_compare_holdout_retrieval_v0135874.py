import unittest
from compare_holdout_retrieval_v0135874 import evaluate

def pair(q,c,yes,label="KNOWN"):
    return dict(query_id=q,candidate_id=c,answer_reusable=str(yes).lower(),proposed_label=label)
def rank(q,c,score):
    return dict(query_id=q,candidate_id=c,score=str(score))
class RetrievalTests(unittest.TestCase):
    def setUp(self):
        self.truth=[pair("1","a",False),pair("1","b",True),
                    pair("2","a",False,"UNKNOWN"),pair("2","b",False,"UNKNOWN")]
        self.ranks=[rank("1","a",0.9),rank("1","b",0.5),
                    rank("2","a",0.7),rank("2","b",0.6)]
    def test_metrics(self):
        r=evaluate(self.truth,self.ranks)
        self.assertEqual(r["hit_at_k_eligible"]["1"],0)
        self.assertEqual(r["hit_at_k_eligible"]["3"],1)
        self.assertEqual(r["mrr_eligible"],0.5)
        self.assertEqual(r["unknown_top1_reusable_count"],0)
    def test_missing_ranking_rejected(self):
        with self.assertRaises(ValueError):evaluate(self.truth,self.ranks[:-1])
    def test_duplicate_rejected(self):
        with self.assertRaises(ValueError):evaluate(self.truth+[self.truth[0]],self.ranks)
    def test_nan_rejected(self):
        ranks=[dict(r) for r in self.ranks];ranks[0]["score"]="nan"
        with self.assertRaises(ValueError):evaluate(self.truth,ranks)
if __name__=="__main__":unittest.main()

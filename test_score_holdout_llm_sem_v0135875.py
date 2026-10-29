import unittest
from score_holdout_llm_sem_v0135875 import cosine, generate
class TestScores(unittest.TestCase):
    def test_cosine(self):
        self.assertAlmostEqual(cosine([1,0],[1,0]),1)
        self.assertAlmostEqual(cosine([1,0],[0,1]),0)
    def test_zero(self):
        with self.assertRaises(ValueError):cosine([0,0],[1,0])
    def test_generate(self):
        rows=[dict(query_id="q",candidate_id="a"),dict(query_id="q",candidate_id="b")]
        vectors={"query":[1,0],"same":[1,0],"other":[0,1]}
        out=generate(rows,{"q":"query"},{"a":"same","b":"other"},lambda s:vectors[s])
        self.assertEqual(len(out),2)
        self.assertGreater(float(out[0]["score"]),float(out[1]["score"]))
    def test_dim(self):
        with self.assertRaises(ValueError):cosine([1],[1,2])
if __name__=="__main__":unittest.main()

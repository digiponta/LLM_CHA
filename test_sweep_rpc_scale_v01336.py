import unittest
from sweep_rpc_scale_v01336 import dispersed_nested,check_split,stable_score

def row(did,turn):
    return {"dialogue_id":did,"utterance_id":turn,"user":"a","assistant":"b"}

class RPCScaleSweepTests(unittest.TestCase):
    def test_deterministic(self):
        rows=[row(10,1),row(10,2),row(30,1),row(20,1)]
        self.assertEqual(dispersed_nested(rows),dispersed_nested(rows))
    def test_preserves_all(self):
        rows=[row(1,i) for i in range(3)]+[row(2,i) for i in range(2)]
        self.assertEqual(len(dispersed_nested(rows)),5)
    def test_round_robin(self):
        rows=[row(1,i) for i in range(4)]+[row(2,i) for i in range(3)]
        sampled=dispersed_nested(rows)
        self.assertEqual(len({r["dialogue_id"] for r in sampled[:2]}),2)
    def test_disjoint(self):
        check_split([row(1,0)],[row(2,0)],[row(3,0)])
        with self.assertRaises(ValueError):
            check_split([row(1,0)],[row(1,1)],[row(3,0)])
    def test_score(self):
        self.assertEqual(stable_score(5),stable_score("5"))
if __name__=="__main__":unittest.main()

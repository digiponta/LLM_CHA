import unittest
from sweep_adapter_capacity_v077 import (
    RANKS,EPOCHS,LEARNING_RATES,select_conditions,condition_id,summarize
)

class SweepTests(unittest.TestCase):
    def test_full_grid(self):
        items=select_conditions()
        self.assertEqual(len(items),27)
        self.assertEqual(len(set(items)),27)
        self.assertEqual(set(r for r,_,_ in items),set(RANKS))
        self.assertEqual(set(e for _,e,_ in items),set(EPOCHS))
        self.assertEqual(set(l for _,_,l in items),set(LEARNING_RATES))
    def test_smoke_subset(self):
        self.assertEqual(len(select_conditions(2)),2)
        with self.assertRaises(ValueError):select_conditions(28)
        with self.assertRaises(ValueError):select_conditions(0)
    def test_distinct_ids(self):
        self.assertEqual(len({condition_id(*row) for row in select_conditions()}),27)
    def test_summary_without_approved_is_not_pass(self):
        def case(route,rank,exact):
            return {"route":route,"first_reference_token_rank":rank,"exact_match":exact}
        diagnostic={"candidate":[{"routes":{"base":case("base",50,False),
            "experimental":case("experimental",10,True)}}],"approved":[]}
        quality={"candidate":{"base":{"mean_nll":4.0},"experimental":{"mean_nll":3.0}},
            "candidate_nll_delta_experimental_minus_base":-1.0}
        row=summarize(diagnostic,quality,8,10,1e-4,"test.pt")
        self.assertIsNone(row["quality_pass"])
        self.assertIsNone(row["approved_exact_experimental"])
        self.assertEqual(row["candidate_exact_experimental"],1.0)
    def test_summary_with_approved(self):
        c={"base":{"first_reference_token_rank":20,"exact_match":False},
           "experimental":{"first_reference_token_rank":2,"exact_match":True}}
        a={"base":{"exact_match":True},"experimental":{"exact_match":True}}
        diagnostic={"candidate":[{"routes":c}],"approved":[{"routes":a}]}
        quality={"candidate":{"base":{"mean_nll":4},"experimental":{"mean_nll":3}},
                 "candidate_nll_delta_experimental_minus_base":-1}
        row=summarize(diagnostic,quality,8,10,1e-4,"test.pt")
        self.assertTrue(row["quality_pass"])
if __name__=="__main__":unittest.main()

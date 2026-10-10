import unittest
from diagnose_algorithmic_copy_errors_v023321 import classify_failure,length_sweep,summarize
class CopyErrorTests(unittest.TestCase):
    def test_exact(self):
        self.assertEqual(classify_failure([10,11,3],[10,11,3],3),"exact")
    def test_early_eos(self):
        self.assertEqual(classify_failure([10,3],[10,11,3],3),"early_eos")
    def test_late_eos(self):
        self.assertEqual(classify_failure([10,11,12,3],[10,11,3],3),"late_eos")
    def test_content_mismatch(self):
        self.assertEqual(classify_failure([10,15,3],[10,11,3],3),"content_mismatch")
    def test_sweep_is_deterministic(self):
        a=length_sweep(1042,list(range(8,72)),3)
        self.assertEqual(a,length_sweep(1042,list(range(8,72)),3))
        self.assertEqual(len(a),17)
        self.assertTrue(all(len(s)==int(name.split("_")[1]) for name,ss in a.items() for s in ss))
    def test_summary(self):
        x={"teacher":{"position_correct":[True,False,True]},
           "free":{"expected_ids":[10,11,3],"exact":False,"prefix_correct":1},
           "first_error_position":1,"failure_type":"content_mismatch"}
        y=summarize([x])
        self.assertEqual(y["total"],1)
        self.assertAlmostEqual(y["teacher_token_top1"],2/3)
        self.assertEqual(y["failure_types"]["content_mismatch"],1)
if __name__=="__main__":unittest.main()

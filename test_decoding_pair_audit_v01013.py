import unittest
from decoding_pair_audit_v01013 import paired_audit

def row(id, method, ok):
    return dict(id=id,method=method,max_new_tokens=48,reference="r",output="r" if ok else "x",
                exact_match=ok,matched_prefix_tokens=1 if ok else 0,
                generated_tokens=1,hit_token_cap=False)

class PairedAuditTests(unittest.TestCase):
    def test_categories_and_net_gain(self):
        records=[]
        for ident,old,new in [("1",1,1),("2",0,1),("3",1,0),("4",0,0),("5",0,1)]:
            records.extend([row(ident,"greedy",old),row(ident,"beam3",new)])
        summary=paired_audit({"records":records})["summary"]
        self.assertEqual(summary["improved"],2)
        self.assertEqual(summary["regressed"],1)
        self.assertEqual(summary["net_gain"],1)
    def test_missing_records_fail_closed(self):
        with self.assertRaisesRegex(ValueError,"Full sweep"):
            paired_audit({"summary":[]})
    def test_unpaired_rejected(self):
        with self.assertRaisesRegex(ValueError,"Unpaired"):
            paired_audit({"records":[row("a","greedy",1),row("b","beam3",1)]})
if __name__=="__main__":
    unittest.main()

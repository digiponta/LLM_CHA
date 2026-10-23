import unittest
from trusted_first_router_v0710 import trusted_first,RouteResult

class TrustedFirstTests(unittest.TestCase):
    def test_trusted_answer_never_calls_experimental(self):
        calls=[]
        def exp(q): calls.append(q);return RouteResult("ANSWER","candidate")
        r=trusted_first("question",lambda q:RouteResult("ANSWER","verified","approved:1"),exp,allow_experimental=True)
        self.assertEqual(r["route"],"TRUSTED")
        self.assertFalse(calls)
    def test_unknown_opt_in_queries_experimental(self):
        calls=[]
        def exp(q):calls.append(q);return RouteResult("ANSWER","candidate","candidate:1")
        r=trusted_first("question",lambda q:RouteResult("UNKNOWN"),exp,allow_experimental=True)
        self.assertEqual(calls,["question"])
        self.assertEqual(r["truth_state"],"EXPERIMENTAL_UNVERIFIED")
        self.assertIn("未承認",r["answer"])
        self.assertFalse(r["auto_promote"])
    def test_unknown_without_optin_blocks(self):
        def forbidden(q):raise AssertionError("not allowed")
        r=trusted_first("question",lambda q:RouteResult("UNKNOWN"),forbidden)
        self.assertEqual(r["route"],"TRUSTED_UNKNOWN")
    def test_both_unknown(self):
        r=trusted_first("question",lambda q:RouteResult("UNKNOWN"),
            lambda q:RouteResult("UNKNOWN"),allow_experimental=True)
        self.assertEqual(r["route"],"EXPERIMENTAL_UNKNOWN")
    def test_invalid_primary_fail_closed(self):
        with self.assertRaises(ValueError):
            trusted_first("question",lambda q:RouteResult("MAYBE","x"),
                lambda q:RouteResult("ANSWER","candidate"),allow_experimental=True)
    def test_missing_question(self):
        with self.assertRaises(ValueError):
            trusted_first("",lambda q:RouteResult("UNKNOWN"),
                lambda q:RouteResult("UNKNOWN"),allow_experimental=True)
if __name__=="__main__":unittest.main()

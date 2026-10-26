import unittest
from unittest.mock import patch
from decoding_sweep_v01012 import sweep,summarize
class Tests(unittest.TestCase):
    def test_matrix_and_no_reference_leak(self):
        fake=type("Result",(),dict(text="answer",token_ids=[1],elapsed_ms=5.0))()
        cases=[dict(id="1",prompt="question",reference="secret")]
        class Tok:
            def encode(self,s,add_bos=False): return [2]
        with patch("decoding_sweep_v01012.decode",return_value=fake) as d:
            rows=sweep(None,Tok(),cases,lengths=(16,32),widths=(1,3,5))
            self.assertEqual(len(rows),6)
            self.assertEqual(len(summarize(rows)),6)
            for c in d.call_args_list:
                self.assertNotIn("secret",str(c))
    def test_caps_and_exact(self):
        fake=type("Result",(),dict(text="yes",token_ids=[1,2],elapsed_ms=5.0))()
        class Tok:
            def encode(self,s,add_bos=False):return [1,2]
        with patch("decoding_sweep_v01012.decode",return_value=fake):
            row=sweep(None,Tok(),[dict(id="1",prompt="q",reference="yes")],lengths=(2,),widths=(1,))[0]
        self.assertTrue(row["hit_token_cap"])
        self.assertTrue(row["exact_match"])
if __name__=="__main__":unittest.main()

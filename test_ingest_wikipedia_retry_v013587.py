import tempfile,unittest,urllib.error
from email.message import Message
from pathlib import Path
from ingest_wikipedia_retry_v013587 import resilient_fetch,retry_seconds

class WikiRetryTests(unittest.TestCase):
    def test_retry_after_seconds(self):
        self.assertEqual(retry_seconds("7",0),7)
    def test_exponential(self):
        self.assertEqual(retry_seconds(None,0),2)
        self.assertEqual(retry_seconds(None,1),4)
    def test_retry_then_cache(self):
        with tempfile.TemporaryDirectory() as d:
            calls=[];waits=[]
            def retrieve(title):
                calls.append(title)
                if len(calls)==1:
                    headers=Message();headers["Retry-After"]="1"
                    raise urllib.error.HTTPError("https://example.invalid",503,"busy",headers,None)
                return {"pageid":42,"title":title}
            r=resilient_fetch("量子力学",retrieve,Path(d),2,waits.append)
            self.assertEqual(r["pageid"],42)
            self.assertEqual(waits,[1.])
            self.assertEqual(resilient_fetch("量子力学",retrieve,Path(d),2,waits.append),r)
            self.assertEqual(len(calls),2)
    def test_bounded_failure(self):
        with tempfile.TemporaryDirectory() as d:
            calls=[]
            def fail(title):
                calls.append(title)
                raise urllib.error.HTTPError("https://example.invalid",503,"busy",Message(),None)
            with self.assertRaises(urllib.error.HTTPError):
                resilient_fetch("量子力学",fail,Path(d),2,lambda _:None)
            self.assertEqual(len(calls),3)
    def test_nonretryable(self):
        with tempfile.TemporaryDirectory() as d:
            calls=[]
            def fail(title):
                calls.append(title)
                raise urllib.error.HTTPError("https://example.invalid",403,"denied",Message(),None)
            with self.assertRaises(urllib.error.HTTPError):
                resilient_fetch("量子力学",fail,Path(d),2,lambda _:None)
            self.assertEqual(len(calls),1)
if __name__=="__main__":unittest.main()

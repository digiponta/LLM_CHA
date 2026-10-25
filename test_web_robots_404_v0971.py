import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from web_acquisition_v097 import acquire

HTML=b"<html><title>Example</title><body>"+b"Public content for testing. "*20+b"</body></html>"
class Response:
    def __init__(self,body):
        self.status=200
        self.headers={"Content-Type":"text/html"}
        self.body=io.BytesIO(body)
    def __enter__(self):return self
    def __exit__(self,*args):self.body.close()
    def read(self,size=-1):return self.body.read(size)
class FakeOpener:
    def __init__(self,robots_code):
        self.robots_code=robots_code
    def open(self,request,timeout=10):
        if request.full_url.endswith("/robots.txt"):
            raise HTTPError(request.full_url,self.robots_code,"error",{},None)
        return Response(HTML)
class Robots404Tests(unittest.TestCase):
    @patch("web_acquisition_v097.validate_url",side_effect=lambda url:url)
    @patch("web_acquisition_v097.urllib.request.build_opener")
    def test_robots_404_allows_html_fetch(self,mock_opener,mock_url):
        mock_opener.return_value=FakeOpener(404)
        with tempfile.TemporaryDirectory() as td:
            r=acquire("https://example.org/",Path(td)/"queue.jsonl")
            self.assertEqual(r["state"],"PENDING_REVIEW")
    @patch("web_acquisition_v097.validate_url",side_effect=lambda url:url)
    @patch("web_acquisition_v097.urllib.request.build_opener")
    def test_robots_503_denied(self,mock_opener,mock_url):
        mock_opener.return_value=FakeOpener(503)
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                acquire("https://example.org/",Path(td)/"queue.jsonl")
if __name__=="__main__":unittest.main()

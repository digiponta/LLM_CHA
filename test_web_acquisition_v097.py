import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from web_acquisition_v097 import validate_url,extract_text,acquire

HTML=b"<html><head><title>Research Test</title></head><body><main>"+b"Evidence only. "*20+b"</main><script>ignore()</script></body></html>"
class AcquisitionTests(unittest.TestCase):
    @patch("web_acquisition_v097.socket.getaddrinfo",return_value=[
        (2,1,6,"",("93.184.216.34",443))])
    def test_public_https(self,mockdns):
        self.assertEqual(validate_url("https://example.org/article"),"https://example.org/article")
    @patch("web_acquisition_v097.socket.getaddrinfo",return_value=[
        (2,1,6,"",("127.0.0.1",443))])
    def test_private_dns_denied(self,mockdns):
        with self.assertRaises(ValueError):
            validate_url("https://example.org/article")
    def test_localhost_denied(self):
        with self.assertRaises(ValueError):
            validate_url("http://localhost/x")
    def test_non_http_denied(self):
        with self.assertRaises(ValueError):
            validate_url("file:///etc/passwd")
    def test_extract(self):
        title,text=extract_text(HTML)
        self.assertEqual(title,"Research Test")
        self.assertNotIn("ignore()",text)
    @patch("web_acquisition_v097.socket.getaddrinfo",return_value=[
        (2,1,6,"",("93.184.216.34",443))])
    def test_pending_only(self,mockdns):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/"review.jsonl"
            r=acquire("https://example.org/article",p,fetcher=lambda url:HTML)
            self.assertEqual(r["state"],"PENDING_REVIEW")
            self.assertFalse(r["train_ready"])
            self.assertFalse(r["auto_promote"])
            self.assertEqual(json.loads(p.read_text(encoding="utf8"))["schema"],"web_pending_v097")
if __name__=="__main__":unittest.main()

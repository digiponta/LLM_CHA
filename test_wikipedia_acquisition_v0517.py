import ast
import unittest
from pathlib import Path
from wikipedia_acquisition_v0517 import lookup

def fake(url):
    if "list=search" in url:
        return {"query":{"search":[{"title":"SQUID"},{"title":"Superconducting quantum interference device"}]}}
    return {"query":{"pages":[{"title":"SQUID","extract":"SQUIDは超伝導を利用した磁束計測装置。磁気センサーとして使用される。"}]}}

class WikipediaAcquisitionTests(unittest.TestCase):
 def test_exact(self):
  r=lookup("SQUID",fetch=fake)
  self.assertEqual(r["status"],"FOUND")
  self.assertEqual(r["title"],"SQUID")
 def test_source(self):
  self.assertEqual(lookup("SQUID",fetch=fake)["source"],"Wikipedia")
 def test_not_verified(self):
  self.assertFalse(lookup("SQUID",fetch=fake)["verified"])
 def test_no_training(self):
  self.assertFalse(lookup("SQUID",fetch=fake)["train_ready"])
 def test_extract(self):
  self.assertIn("超伝導",lookup("SQUID",fetch=fake)["extract"])
 def test_url(self):
  self.assertIn("ja.wikipedia.org/wiki/SQUID",lookup("SQUID",fetch=fake)["url"])
 def test_not_found(self):
  r=lookup("SQUID",fetch=lambda _:{"query":{"search":[]}})
  self.assertEqual(r["status"],"NOT_FOUND")
 def test_ambiguous(self):
  r=lookup("ABC",fetch=lambda _:{"query":{"search":[{"title":"ABC放送"},{"title":"ABC理論"}]}})
  self.assertEqual(r["status"],"AMBIGUOUS")
 def test_network_failure(self):
  def fail(_):raise TimeoutError()
  self.assertEqual(lookup("SQUID",fetch=fail)["status"],"LOOKUP_FAILED")
 def test_invalid_term(self):
  with self.assertRaises(ValueError):lookup("")
 def test_chat_syntax(self):
  src=(Path(__file__).parent/"chat.py").read_text(encoding="utf-8")
  ast.parse(src)
  self.assertIn("cha_wikipedia_lookup(term)",src)
 def test_legacy_sleep(self):
  src=(Path(__file__).parent/"chat.py").read_text(encoding="utf-8")
  self.assertIn('if command == "/sleep":',src)
if __name__=="__main__":unittest.main()

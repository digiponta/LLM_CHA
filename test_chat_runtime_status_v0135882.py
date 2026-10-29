import tempfile, unittest
from pathlib import Path
from chat_runtime_status_v0135882 import get_status,status_text
class StatusTests(unittest.TestCase):
 def test_no_source(self):
  with tempfile.TemporaryDirectory() as d:
   s=get_status(d)
   self.assertEqual(s["approved_source_count"],0)
   self.assertIn("DISABLED",s["verifier"])
 def test_status_output(self):
  with tempfile.TemporaryDirectory() as d:
   self.assertIn("v0.13.58.82",status_text(d))
if __name__=="__main__":unittest.main()

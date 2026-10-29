import tempfile,unittest,csv
from pathlib import Path
from audit_unknown_gate_v0135866 import prepare,load_cases,metrics,audit
class Tests(unittest.TestCase):
 def test_prepare_pending(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"labels.csv"
   prepare(p,[{"id":"h","user":"こんにちは"}])
   with self.assertRaises(ValueError):load_cases(p)
 def test_metrics(self):
  x=[{"expected":"KNOWN","accepted":True},{"expected":"UNKNOWN","accepted":False}]
  z=metrics(x)
  self.assertEqual(z["known_coverage"],1)
  self.assertEqual(z["unknown_reject_rate"],1)
 def test_audit(self):
  train=[{"id":"a","user":"こんにちは","assistant":"やあ"}]
  cases=[{"id":"known","question":"こんにちは","expected":"KNOWN"},
         {"id":"unknown","question":"XYZ","expected":"UNKNOWN"}]
  h=[[{"rank":1,"id":"a","question":"こんにちは","answer":"やあ","score":.96}],
     [{"rank":1,"id":"a","question":"こんにちは","answer":"やあ","score":.12}]]
  result=audit(train,cases,h,[(.85,0)],[("ruri",(0,0))])
  self.assertEqual(result[0]["metrics"]["known_coverage"],1)
  self.assertEqual(result[0]["metrics"]["unknown_reject_rate"],1)
if __name__=="__main__":unittest.main()

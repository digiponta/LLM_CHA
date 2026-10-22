import unittest
from history_evidence_rank_v0625 import history_events
class HistoryRankTests(unittest.TestCase):
 def test_rank(self):
  sentences=["トヨタはモビリティカンパニーを目指す。",
             "1950年に工場の生産を開始した。",
             "1937年に会社を設立した。"]
  self.assertEqual(history_events(sentences)[0],"1937年に会社を設立した。")
 def test_no_date(self):
  self.assertEqual(history_events(["歴史のある会社として発展した。"]),[])
 def test_markup(self):
  self.assertEqual(history_events(["</ref> 1937年に設立した。"]),[])
if __name__=="__main__":unittest.main()

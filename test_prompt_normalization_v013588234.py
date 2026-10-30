import io
import unittest
from llm_input_channel_v013588233 import normalize_one_line,send_one_line

class Proc:
 def __init__(self):self.stdin=io.BytesIO()
 def poll(self):return None

class Tests(unittest.TestCase):
 def test_normalization(self):
  self.assertEqual(normalize_one_line("話題：宇宙\n資料：膨張\r\n回答："),"話題：宇宙 資料：膨張 回答：")
 def test_send_one_request(self):
  p=Proc()
  send_one_line(p,"話題：宇宙\n資料：膨張\n回答：")
  self.assertEqual(p.stdin.getvalue().count(b"\n"),1)
 def test_empty_rejected(self):
  with self.assertRaisesRegex(ValueError,"PROMPT_EMPTY"):
   send_one_line(Proc(),"\n \t")
 def test_no_embedded_linebreak(self):
  prompt=normalize_one_line("宇宙\u2028膨張\u2029回答")
  self.assertNotIn("\u2028",prompt);self.assertNotIn("\u2029",prompt)
if __name__=="__main__":unittest.main()

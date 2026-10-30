import io
import unittest
from llm_input_channel_v013588233 import send_one_line
class Proc:
 def __init__(self,stream=None,exit_code=None):
  self.stdin=stream if stream is not None else io.BytesIO()
  self.exit_code=exit_code
 def poll(self):return self.exit_code
class Tests(unittest.TestCase):
 def test_success(self):
  p=Proc();send_one_line(p,"宇宙を説明");self.assertEqual(p.stdin.getvalue(),"宇宙を説明\n".encode())
 def test_multiline_rejected(self):
  p=Proc()
  with self.assertRaisesRegex(ValueError,"PROMPT_MULTILINE"):send_one_line(p,"話題\n資料")
  self.assertEqual(p.stdin.getvalue(),b"")
 def test_closed_stdin(self):
  p=Proc();p.stdin.close()
  with self.assertRaisesRegex(ValueError,"STDIN_UNAVAILABLE"):send_one_line(p,"宇宙")
 def test_stopped(self):
  with self.assertRaisesRegex(RuntimeError,"PROCESS_NOT_RUNNING"):send_one_line(Proc(exit_code=1),"宇宙")
if __name__=="__main__":unittest.main()

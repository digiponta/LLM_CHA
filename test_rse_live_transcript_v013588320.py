import json,tempfile,unittest
from pathlib import Path
from compare_rse_live_transcript_v013588320 import parse_transcript,evaluate
class LiveTranscriptTests(unittest.TestCase):
 def test_parse_console(self):
  rows=parse_transcript("You> 閃亜鉛鉱とは\nAI> 閃亜鉛鉱は、亜鉛の硫化鉱物である。\n[route=UNIFIED]\nYou> 今何してる？\nAI> 未学習です\n")
  self.assertEqual(len(rows),2)
  self.assertEqual(rows[0]["route_lines"],["[route=UNIFIED]"])
 def test_evaluate_real_observed_not_synthesized(self):
  with tempfile.TemporaryDirectory() as d:
   u=Path(d)/"u.jsonl";truth=Path(d)/"truth.jsonl"
   u.write_text(json.dumps({"concept":"閃亜鉛鉱","assistant":"閃亜鉛鉱は、亜鉛の硫化鉱物である。"},ensure_ascii=False)+"\n",encoding="utf-8")
   truth.write_text("",encoding="utf-8")
   turns=parse_transcript("You> 閃亜鉛鉱とは\nAI> 閃亜鉛鉱は、亜鉛の硫化鉱物である。\nYou> 今何してる？\nAI> 未学習です\n")
   x=evaluate(turns,u,truth,[])
   self.assertEqual(x["cases"][0]["classification"],"UNIFIED_MATCH_OBSERVED")
   self.assertEqual(x["cases"][1]["rse_state"],"UNLEARNED")
   self.assertFalse(x["chat_py_executed_by_this_script"])
 def test_missing_answer_is_not_imputed(self):
  with tempfile.TemporaryDirectory() as d:
   u=Path(d)/"u.jsonl";t=Path(d)/"t.jsonl"
   u.write_text("",encoding="utf-8");t.write_text("",encoding="utf-8")
   x=evaluate(parse_transcript("You> 今何してる？\n"),u,t,[])
   self.assertEqual(x["cases"][0]["classification"],"NO_OBSERVED_ANSWER")
if __name__=="__main__":unittest.main()

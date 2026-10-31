import json,tempfile,unittest
from pathlib import Path
from audit_real_persona_pairs_v013588292 import extract_pairs,analyze,split_for_dialogue
class PairAuditTests(unittest.TestCase):
 def test_direction_and_repeated_speaker(self):
  d={"interlocutors":["A","B"],"utterances":[{"interlocutor_id":"A","text":"hello"},{"interlocutor_id":"B","text":"hi"},{"interlocutor_id":"B","text":"same"},{"interlocutor_id":"A","text":"great"}]}
  pairs,error=extract_pairs(d)
  self.assertIsNone(error);self.assertEqual([(a,b) for a,b,_ in pairs],[("hello","hi"),("same","great")])
 def test_unknown_speaker_rejected(self):
  d={"interlocutors":["A","B"],"utterances":[{"interlocutor_id":"X","text":"hi"}]}
  self.assertEqual(extract_pairs(d)[1],"BAD_SPEAKER_IDS")
 def test_split_is_stable(self):self.assertEqual(split_for_dialogue("001"),split_for_dialogue("001"))
 def test_text_not_exported(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"real_persona_chat"/"dialogues";p.mkdir(parents=True)
   (p/"001.json").write_text(json.dumps({"dialogue_id":"001","interlocutors":["A","B"],"utterances":[{"interlocutor_id":"A","text":"private input"},{"interlocutor_id":"B","text":"private output"}]}))
   x=analyze(d)
   self.assertEqual(x["counts"]["usable_pairs"],1);self.assertNotIn("private output",json.dumps(x))
if __name__=="__main__":unittest.main()

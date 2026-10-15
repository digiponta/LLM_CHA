import ast
import unittest
from pathlib import Path
from wiki_relation_alignment_v0535 import align
Q="なぜSQUIDは高感度なの？"
URL="https://ja.wikipedia.org/wiki/超伝導量子干渉計"
class AlignmentTests(unittest.TestCase):
 def test_aligned(self):
  r=align(Q,"SQUIDのジョセフソン接合によって磁場感度が向上することが可能になる",URL)
  self.assertEqual(r["status"],"ALIGNED_CANDIDATE")
  self.assertFalse(r["causal_answer_approved"])
 def test_mri_rejected(self):
  r=align(Q,"SQUIDの高感度によってMRI撮像が可能になる",URL)
  self.assertEqual(r["status"],"NO_ALIGNED_CAUSAL_EVIDENCE")
  self.assertEqual(r["candidates"][0]["reason"],"DOWNSTREAM_EFFECT_NOT_SENSITIVITY")
 def test_unrelated_cause(self):
  r=align(Q,"SQUIDの回路故障が原因で測定誤差が生じる",URL)
  self.assertEqual(r["candidates"][0]["reason"],"TARGET_EFFECT_MISMATCH")
 def test_missing_device(self):
  r=align(Q,"ジョセフソン接合によって磁場感度が向上することが可能になる",URL)
  self.assertEqual(r["candidates"][0]["reason"],"SUBJECT_NOT_GROUNDED")
 def test_nonphysical(self):
  r=align(Q,"SQUIDの価格によって磁場感度が向上することが可能になる",URL)
  self.assertEqual(r["candidates"][0]["reason"],"CAUSE_NOT_GROUNDED_IN_DEVICE")
 def test_structure_only(self):
  self.assertEqual(align(Q,"SQUIDとはジョセフソン接合を含む環状超伝導体に基く。",URL)["status"],"NO_ALIGNED_CAUSAL_EVIDENCE")
 def test_unrelated_question(self):
  self.assertEqual(align("何に使う？","SQUIDの高感度によってMRI撮像が可能になる",URL)["status"],"NOT_APPLICABLE")
 def test_readonly(self):
  r=align(Q,"SQUIDのジョセフソン接合によって磁場感度が向上することが可能になる",URL)
  self.assertFalse(r["verified"]);self.assertFalse(r["train_ready"])
 def test_provenance(self):
  r=align(Q,"SQUIDのジョセフソン接合によって磁場感度が向上することが可能になる",URL)
  self.assertEqual(r["candidates"][0]["source"],URL)
 def test_chat_syntax(self):
  code=(Path(__file__).parent/"chat.py").read_text(encoding="utf-8")
  ast.parse(code)
  self.assertIn("wiki_relation_alignment=",code)
if __name__=="__main__":unittest.main()

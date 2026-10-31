import json,tempfile,unittest
from pathlib import Path
from review_real_persona_quality_v013588294 import profile_metadata
class QualityReviewTests(unittest.TestCase):
 def test_missing_profile(self):
  with tempfile.TemporaryDirectory() as d:self.assertEqual(profile_metadata(d,"CP")["status"],"PROFILES_FILE_NOT_FOUND")
 def test_profile_fields_no_values(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"interlocutors.json";p.write_text(json.dumps({"CP":{"description":"PRIVATE_TEXT","age":20}}))
   x=profile_metadata(d,"CP")
   self.assertEqual(x["field_names"],["description","age"])
   self.assertNotIn("PRIVATE_TEXT",json.dumps(x))
 def test_unknown_speaker(self):
  with tempfile.TemporaryDirectory() as d:
   (Path(d)/"interlocutors.json").write_text(json.dumps({"AA":{}}))
   self.assertEqual(profile_metadata(d,"CP")["status"],"SPEAKER_NOT_IN_PROFILES")
if __name__=="__main__":unittest.main()

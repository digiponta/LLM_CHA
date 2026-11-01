import unittest,tempfile,json
from pathlib import Path
from diagnose_rse_proposition_compose_v013588316 import diagnose,duplicate
class Tests(unittest.TestCase):
 def test_duplicate(self):
  self.assertTrue(duplicate("鉱物であるである。"))
  self.assertFalse(duplicate("鉱物である。"))
 def test_pipeline(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)
   def put(name,rows):
    p=root/name
    p.write_text("".join(json.dumps(x,ensure_ascii=False)+"\n" for x in rows),encoding="utf-8")
    return p
   a=put("a",[{"subject":"閃亜鉛鉱","value":"亜鉛の硫化鉱物である"}])
   si=put("s",[{"subject":"閃亜鉛鉱","value":"亜鉛の硫化鉱物である","statement":"閃亜鉛鉱は亜鉛の硫化鉱物であるである。"}])
   ti=put("t",[{"subject":"閃亜鉛鉱","value":"亜鉛の硫化鉱物である","statement":"閃亜鉛鉱は亜鉛の硫化鉱物であるである。","predicate_type":"property"}])
   u=put("u",[{"concept":"閃亜鉛鉱","assistant":"閃亜鉛鉱は、亜鉛の硫化鉱物であるである。"}])
   x=diagnose("閃亜鉛鉱",a,si,ti,u)
   self.assertEqual(x["possible_mechanism"],"VALUE_ALREADY_HAS_COPULA")
   self.assertIn("unified_answers",x["flags"]["duplicated_at"])
   self.assertFalse(x["stores_modified"])
if __name__=="__main__":unittest.main()

import bz2,json,tempfile,unittest
from pathlib import Path
from extract_jawiki_dump_v0135818 import clean_wikitext,stream_articles,run

XML='''<mediawiki xmlns="http://www.mediawiki.org/xml/export-0.11/">
<page><title>テスト記事</title><ns>0</ns><id>42</id><revision><text xml:space="preserve">'''+"これは[[日本語]]の百科事典に関する説明です。 "*12+'''</text></revision></page>
<page><title>転送先</title><ns>0</ns><id>43</id><revision><text>#転送 [[テスト記事]]</text></revision></page>
<page><title>利用者:サンプル</title><ns>2</ns><id>44</id><revision><text>対象外</text></revision></page>
</mediawiki>'''
class Tests(unittest.TestCase):
 def test_clean_markup(self):
  x=clean_wikitext("導入 {{注釈|foo={{bar}}}} [[日本語|和文]] <ref>出典</ref> 結末")
  self.assertIn("和文",x)
  self.assertNotIn("foo",x)
  self.assertNotIn("出典",x)
 def test_stream_bz2_and_filters(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/"sample.xml.bz2"
   p.write_bytes(bz2.compress(XML.encode("utf8")))
   rows=list(stream_articles(p,2,20))
   self.assertEqual(len(rows),1)
   self.assertEqual(rows[0]["page_id"],"42")
 def test_artifact_manifest_safety(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/"sample.xml.bz2";p.write_bytes(bz2.compress(XML.encode("utf8")))
   dest=Path(tmp)/"out"
   m=run(p,dest,1,20)
   self.assertFalse(m["training_performed"])
   self.assertFalse(m["memory_promoted"])
   item=json.loads((dest/"jawiki_semantic_candidates.jsonl").read_text(encoding="utf8").splitlines()[0])
   self.assertFalse(item["auto_promote"])
   self.assertEqual(item["page_id"],"42")
   with self.assertRaises(FileExistsError):run(p,dest,1,20)
 def test_invalid_limits(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/"sample.xml.bz2";p.write_bytes(bz2.compress(XML.encode("utf8")))
   with self.assertRaises(ValueError):list(stream_articles(p,0,20))
if __name__=="__main__":unittest.main()

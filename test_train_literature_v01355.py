import hashlib,json,tempfile,unittest
from pathlib import Path
from train_literature_v01355 import prepare

class LiteratureTests(unittest.TestCase):
    def make_case(self,d):
        p=Path(d);source=p/"literature.txt";audit=p/"audit.json"
        rows=[f"実験用の文章{i}。" for i in range(120)]
        source.write_text("\n".join(rows)+"\n",encoding="utf-8")
        meta={"version":"v0.13.54","status":"DIFF_VERIFIED",
              "after_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),
              "sentences_after":120}
        audit.write_text(json.dumps(meta),encoding="utf-8")
        return source,audit
    def test_partition(self):
        with tempfile.TemporaryDirectory() as d:
            s,a=self.make_case(d);train,val,info=prepare(s,a)
            self.assertEqual((len(train),len(val)),(114,6))
            self.assertFalse(info["source_independence_verified"])
            self.assertFalse(info["training_approved"])
    def test_hash_mismatch(self):
        with tempfile.TemporaryDirectory() as d:
            s,a=self.make_case(d);s.write_text("tampered",encoding="utf-8")
            with self.assertRaises(ValueError):prepare(s,a)
    def test_bad_status(self):
        with tempfile.TemporaryDirectory() as d:
            s,a=self.make_case(d);j=json.loads(a.read_text());j["status"]="REVIEW_REQUIRED"
            a.write_text(json.dumps(j),encoding="utf-8")
            with self.assertRaises(ValueError):prepare(s,a)
    def test_fraction(self):
        with tempfile.TemporaryDirectory() as d:
            s,a=self.make_case(d)
            with self.assertRaises(ValueError):prepare(s,a,val_fraction=.5)
    def test_contiguous_split(self):
        with tempfile.TemporaryDirectory() as d:
            s,a=self.make_case(d);train,val,_=prepare(s,a)
            self.assertEqual(val[-1],"実験用の文章119。")
            self.assertEqual(train[0],"実験用の文章0。")
if __name__=="__main__":unittest.main()

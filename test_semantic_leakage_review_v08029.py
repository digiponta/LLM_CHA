import json
import tempfile
import unittest
from pathlib import Path
from semantic_leakage_review_v08029 import review

class SemanticVectorTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root=Path(self.tmp.name)
        self.source,self.store,self.vectors=(root/"h.json",root/"t.json",root/"v.json")
        self.source.write_text(json.dumps({"records":[{"id":"h1","evaluation_kind":"UNSEEN_FACT",
            "question":"月面の地形","reference_answer":"クレーター",
            "source_url":"https://example.org","source_excerpt":"Crater"}]},ensure_ascii=False),encoding="utf-8")
        self.store.write_text(json.dumps({"candidates":[{"id":"t1","subject":"金星",
            "natural_language":"金星の大気"}]},ensure_ascii=False),encoding="utf-8")
    def payload(self,hvec,tvec):
        return {"embedding_space":{"model_id":"llm-sem-test","checkpoint_sha256":"a"*64,
           "tokenizer_sha256":"b"*64,"pooling":"mean","normalization":"l2",
           "dimension":2},"vectors":[{"kind":"training","id":"t1","values":tvec},
                          {"kind":"holdout","id":"h1","values":hvec}]}
    def write(self,payload):
        self.vectors.write_text(json.dumps(payload),encoding="utf-8-sig")
    def test_missing_vectors_does_not_approve(self):
        r=review(self.source,self.store)
        self.assertEqual(r["vector_analysis_status"],"VECTORS_NOT_PROVIDED")
        self.assertFalse(r["formal_holdout_approved"])
    def test_same_direction_flags_overlap(self):
        self.write(self.payload([1,0],[2,0]))
        r=review(self.source,self.store,self.vectors,0.9)
        self.assertEqual(r["vector_analysis_status"],"VECTOR_SCREEN_COMPLETED")
        self.assertTrue(r["vector_results"][0]["possible_overlap"])
        self.assertFalse(r["semantic_independence_verified"])
    def test_orthogonal_not_certificate(self):
        self.write(self.payload([1,0],[0,1]))
        r=review(self.source,self.store,self.vectors,0.9)
        self.assertFalse(r["vector_results"][0]["possible_overlap"])
        self.assertFalse(r["formal_holdout_approved"])
    def test_missing_id_rejected(self):
        p=self.payload([1,0],[1,0]);p["vectors"].pop()
        self.write(p)
        self.assertEqual(review(self.source,self.store,self.vectors,0.9)["vector_analysis_status"],
                         "INVALID_VECTOR_INPUT")
    def test_nonfinite_rejected(self):
        self.write(self.payload([float("nan"),0],[1,0]))
        self.assertEqual(review(self.source,self.store,self.vectors,0.9)["vector_analysis_status"],
                         "INVALID_VECTOR_INPUT")
    def test_uncalibrated_threshold_not_run(self):
        self.write(self.payload([1,0],[1,0]))
        self.assertEqual(review(self.source,self.store,self.vectors)["vector_analysis_status"],
                         "THRESHOLD_NOT_CALIBRATED")

if __name__=="__main__":
    unittest.main()

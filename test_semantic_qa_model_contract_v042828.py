import unittest
from semantic_qa_model_contract_v042828 import design,validate_predictions

class Tests(unittest.TestCase):
    def fixture(self):
        records=[{"id":f"T{i:02d}","turn":1,"question":"GPUって何？",
          "final_answer":"GPUは並列処理装置。","gate_resolution":"ACCEPT",
          "candidate_alignment":"SINGLE_TURN_CONFIRMED","literal_probe_identity":False,
          "manual_review":{}} for i in range(64)]
        validation={"records":records}
        labels={"schema":"llm_cha_chatgpt_qa_v1","label_source":"chatgpt",
          "decisions":[{"id":r["id"],"turn":1,"relevant":True,"reason":"説明している"} for r in records]}
        predictions={"schema":"llm_cha_semantic_qa_predictions_v1","method":"cross_encoder",
          "dataset_split":"DEVELOPMENT_ONLY","predictions":[{"id":r["id"],"turn":1,
          "decision":"ABSTAIN","score":None} for r in records]}
        return validation,labels,predictions
    def test_contract_no_training(self):
        v,l,_=self.fixture();r=design(v,l)
        self.assertEqual(r["total"],64)
        self.assertFalse(r["model_inference_executed"])
        self.assertFalse(r["model_trained"])
    def test_valid_prediction_import(self):
        v,l,p=self.fixture();r=validate_predictions(design(v,l),p)
        self.assertEqual(r["total"],64)
        self.assertEqual(r["scored"],0)
    def test_duplicate_rejected(self):
        v,l,p=self.fixture();p["predictions"][0]["id"]="T01"
        with self.assertRaises(ValueError):validate_predictions(design(v,l),p)
    def test_invalid_score_rejected(self):
        v,l,p=self.fixture();p["predictions"][0]["decision"]="RELEVANT"
        p["predictions"][0]["score"]=1.2
        with self.assertRaises(ValueError):validate_predictions(design(v,l),p)
    def test_no_claimed_holdout(self):
        v,l,p=self.fixture();p["dataset_split"]="TEST"
        with self.assertRaises(ValueError):validate_predictions(design(v,l),p)
    def test_provisional_labels_not_ground_truth(self):
        v,l,_=self.fixture();r=design(v,l)
        self.assertFalse(r["human_ground_truth"])
        self.assertFalse(r["independent_holdout"])
if __name__=="__main__":unittest.main()

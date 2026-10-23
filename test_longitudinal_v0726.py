import tempfile,unittest,json
from pathlib import Path
from benchmark_longitudinal_v0726 import validate_probes,compare
class LongitudinalTests(unittest.TestCase):
    def setUp(self):
        self.probes=[
          {"knowledge_id":"A","split":"train","question":"Aの符号","reference":"AO-17"},
          {"knowledge_id":"A","split":"paraphrase","question":"符号Aを教えて","reference":"AO-17"},
          {"knowledge_id":"B","split":"train","question":"Bの符号","reference":"RB-42"}]
    def test_valid(self):
        self.assertEqual(len(validate_probes(self.probes)),3)
    def test_duplicate_rejected(self):
        with self.assertRaises(ValueError):validate_probes(self.probes+self.probes[:1])
    def test_forgetting_detected(self):
        def factory(path):
            responses={"before":{"Aの符号":"AO-17","符号Aを教えて":"AO-17","Bの符号":"不明"},
                       "after":{"Aの符号":"誤り","符号Aを教えて":"AO-17","Bの符号":"RB-42"}}
            return lambda q:responses[path][q]
        report=compare(["before","after"],self.probes,factory)
        self.assertEqual(report["initially_correct"],2)
        self.assertEqual(report["lost_correct"],1)
        self.assertEqual(report["forgetting_rate"],0.5)
    def test_single_checkpoint_not_forgetting(self):
        r=compare(["before"],self.probes,lambda path:lambda q:"不明")
        self.assertFalse(r["forgetting_measurable"])
        self.assertIsNone(r["forgetting_rate"])
    def test_train_paraphrase_metrics(self):
        r=compare(["after"],self.probes,lambda path:lambda q:{"Aの符号":"AO-17",
           "符号Aを教えて":"違う","Bの符号":"RB-42"}[q])
        self.assertEqual(r["checkpoints"][0]["metrics"]["train"]["exact"],2)
        self.assertEqual(r["checkpoints"][0]["metrics"]["paraphrase"]["exact"],0)
if __name__=="__main__":unittest.main()

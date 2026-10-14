import unittest
from run_generation_ablation_v042854 import make_prompt,run_experiment

class FakeTorch: pass
class FakeTokenizer:
    eos_id=2
    def encode(self,text,add_bos=False):
        return [1]+list(text.encode("utf-8")) if add_bos else list(text.encode("utf-8"))
    def decode(self,ids):
        return bytes(ids).decode("utf-8")
class FakeModel:
    def generate(self,ids,**kwargs):
        return ids+list("こんにちは".encode("utf-8"))

def data(valid=True):
    return {"version":"v0.4.28.53","train_ready":False,
        "examples":[{"id":"1","source_line":1,"train_eligible":False,
                     "full_context":"人: A\n相手: B\n人: C",
                     "last_user_only":"C" if valid else None}]}

class GenerationAblationTests(unittest.TestCase):
    def test_prompt(self):
        self.assertEqual(make_prompt("ABC"),"ABC\n相手: ")
    def test_unsafe_reject(self):
        import unittest.mock as mock
        with mock.patch.dict("sys.modules",{"torch":mock.MagicMock()}):
            x=data();x["train_ready"]=True
            with self.assertRaises(ValueError):run_experiment(x,FakeModel(),FakeTokenizer(),device="cpu")
    def test_paired(self):
        import unittest.mock as mock
        with mock.patch.dict("sys.modules",{"torch":mock.MagicMock()}):
            r=run_experiment(data(),FakeModel(),FakeTokenizer(),device="cpu")
            self.assertEqual(r["paired_generations"],1)
            self.assertIsNone(r["accuracy"])
            self.assertFalse(r["train_ready"])
    def test_invalid_arm(self):
        import unittest.mock as mock
        with mock.patch.dict("sys.modules",{"torch":mock.MagicMock()}):
            r=run_experiment(data(False),FakeModel(),FakeTokenizer(),device="cpu")
            self.assertEqual(r["paired_generations"],0)
            self.assertEqual(r["results"][0]["variants"]["last_user_only"]["status"],"not_applicable")
if __name__=="__main__": unittest.main()

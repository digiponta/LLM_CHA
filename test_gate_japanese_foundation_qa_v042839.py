import unittest
from gate_japanese_foundation_qa_v042839 import evaluate,gate

def case(answer,rule="likes"):
    return {"id":"JF38-00001","question":"暫定質問","answer":answer,
            "generation_rule":rule,"proposed_label":True,
            "source":{"file":"data/japanese_foundation_v0218.txt","line":1}}
class Tests(unittest.TestCase):
    def test_identity_rejected(self):
        r=evaluate(case("私はコーヒーが大好きです。","identity"))
        self.assertEqual(r["gate_status"],"REJECT")
    def test_identity_weather_rejected(self):
        r=evaluate(case("私は九州に住んでいるので、今は台風一過で快晴です。","identity"))
        self.assertEqual(r["gate_status"],"REJECT")
    def test_simple_preference_held(self):
        r=evaluate(case("私はコーヒーが好きです。"))
        self.assertEqual(r["gate_status"],"HOLD")
        self.assertEqual(r["suggested_question"],"コーヒーが好きですか。")
    def test_compound_held_after_clause_extract(self):
        r=evaluate(case("さつまいもいいですね。さつまいもご飯が好きです。"))
        self.assertEqual(r["gate_status"],"HOLD")
        self.assertEqual(r["suggested_question"],"さつまいもご飯が好きですか。")
    def test_pronoun_rejected(self):
        r=evaluate(case("それが好きです。"))
        self.assertEqual(r["gate_status"],"REJECT")
    def test_comma_rejected(self):
        r=evaluate(case("普通のスパゲティ、ペンネ、フェットチーネが好きです。"))
        self.assertEqual(r["gate_status"],"REJECT")
    def test_no_accept_without_review(self):
        d=gate({"version":"v0.4.28.38","candidates":[case("私は漫画が好きです。")]})
        self.assertEqual(d["accepted"],0)
        self.assertFalse(d["train_ready"])
        self.assertEqual(d["total"],1)
    def test_preserve_source(self):
        r=evaluate(case("僕は映画が好きです。"))
        self.assertEqual(r["source"]["line"],1)
        self.assertEqual(r["answer"],"僕は映画が好きです。")
if __name__=="__main__":unittest.main()

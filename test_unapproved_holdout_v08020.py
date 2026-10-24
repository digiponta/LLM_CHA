import unittest
from pathlib import Path
from unapproved_holdout_v08020 import validate_holdout

TRAIN=[{"id":"train1","subject":"量子ビット",
        "natural_language":"量子ビットは基本単位である。"}]
class HoldoutContractTests(unittest.TestCase):
    def test_valid_external_record(self):
        data={"records":[{"id":"outside1","question":"新規対象を説明して",
                           "reference_answer":"別の検証用回答です。"}]}
        self.assertEqual(len(validate_holdout(data,TRAIN,["train1"])),1)
    def test_id_leakage(self):
        data={"records":[{"id":"train1","question":"新規対象",
                           "reference_answer":"新規回答"}]}
        with self.assertRaisesRegex(ValueError,"TRAINING_ID_LEAKAGE"):
            validate_holdout(data,TRAIN,["train1"])
    def test_answer_leakage(self):
        data={"records":[{"id":"new","question":"別の質問",
                           "reference_answer":"Wikipediaの未検証情報: 量子ビットは基本単位である。"}]}
        with self.assertRaisesRegex(ValueError,"TRAINING_ANSWER_LEAKAGE"):
            validate_holdout(data,TRAIN,["train1"])
    def test_empty_rejected(self):
        with self.assertRaisesRegex(ValueError,"EMPTY_HOLDOUT"):
            validate_holdout({"records":[]},TRAIN,["train1"])
    def test_runtime_and_gui(self):
        chat=Path(__file__).with_name("chat.py").read_text(encoding="utf-8")
        gui=Path(__file__).with_name("chat_gui_v07447.py").read_text(encoding="utf-8")
        self.assertIn('if user_text == "/wiki-model-holdout":',chat)
        self.assertIn('request_status("/wiki-model-holdout")',gui)
        for file in ("chat.py","chat_gui_v07447.py","unapproved_holdout_v08020.py"):
            compile(Path(__file__).with_name(file).read_text(encoding="utf-8"),file,"exec")
if __name__=="__main__":unittest.main()

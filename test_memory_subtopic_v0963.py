import unittest
from memory_subtopic_v0963 import classify,retrieve
from memory_opinion_experiment_v0963 import evaluate_memory_opinion

CORPUS=("サーバ仮想化では仮想メモリのアドレスに仮想サーバー識別番号を追加する。\n"
        "実行中の命令を保持するメモリのアドレス値を追跡する。\n"
        "脳の外部記憶とUSBメモリについて考察した。\n"
        "オンメモリDBMSの三重化はリスクがある。")
class MemorySubtopicTests(unittest.TestCase):
    def test_virtual(self):
        self.assertEqual(classify("仮想メモリのアドレス"),"VIRTUAL_MEMORY")
    def test_external(self):
        self.assertEqual(classify("USBメモリを外部記憶に"),"EXTERNAL_MEMORY")
    def test_database(self):
        self.assertEqual(classify("オンメモリDBMSの三重化"),"DATABASE_MEMORY")
    def test_retrieve(self):
        self.assertGreaterEqual(len(retrieve("メモリ",CORPUS)),3)
    def test_selected_subtopic(self):
        self.assertEqual(len(retrieve("メモリ",CORPUS,"DATABASE_MEMORY")),1)
    def test_not_foreign_topic(self):
        self.assertEqual(retrieve("量子力学",CORPUS),[])
    def test_template_provenance(self):
        r=evaluate_memory_opinion("メモリ",retrieve("メモリ",CORPUS),"従来の回答")
        self.assertEqual(r["candidate_origin"],"DETERMINISTIC_TEMPLATE_NOT_LLM")
        self.assertFalse(r["train_ready"])
    def test_no_evidence_baseline(self):
        r=evaluate_memory_opinion("メモリ",[],"従来の回答")
        self.assertEqual(r["selected"],"従来の回答")
if __name__=="__main__":unittest.main()

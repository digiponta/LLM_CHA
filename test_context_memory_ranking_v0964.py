import unittest
from context_memory_ranking_v0964 import ranked_from_corpus
from memory_opinion_experiment_v0963 import evaluate_memory_opinion

CORPUS=("脳組織において二者択一な記憶が生じる。\n"
        "サーバ仮想化で仮想メモリのアドレスを使う。\n"
        "命令が置かれたメモリのアドレス値を調べる。\n"
        "外部記憶をUSBメモリで実現する。\n"
        "オンメモリDBMSの三重化にはリスクがある。")
class MemoryContextRankTests(unittest.TestCase):
    def test_selected_storage_prefers_cpu(self):
        r=ranked_from_corpus("メモリ",CORPUS,"記憶装置")
        self.assertIn(r[0]["subtopic"],("CPU_MEMORY","VIRTUAL_MEMORY"))
        self.assertNotEqual(r[0]["subtopic"],"BIOLOGICAL_MEMORY")
    def test_flash_prefers_external(self):
        self.assertEqual(ranked_from_corpus("メモリ",CORPUS,"フラッシュメモリ")[0]["subtopic"],"EXTERNAL_MEMORY")
    def test_no_context_preserves_document_order(self):
        self.assertEqual(ranked_from_corpus("メモリ",CORPUS)[0]["subtopic"],"BIOLOGICAL_MEMORY")
    def test_original_position_preserved(self):
        r=ranked_from_corpus("メモリ",CORPUS,"記憶装置")
        self.assertGreaterEqual(r[0]["position"],0)
        self.assertFalse(r[0]["verified"])
    def test_ab_uses_ranked_first(self):
        r=ranked_from_corpus("メモリ",CORPUS,"記憶装置")
        result=evaluate_memory_opinion("メモリ",r,"元の回答")
        self.assertEqual(result["subtopic"],r[0]["subtopic"])
        self.assertEqual(result["candidate_origin"],"DETERMINISTIC_TEMPLATE_NOT_LLM")
if __name__=="__main__":unittest.main()

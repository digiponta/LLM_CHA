import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from diagnose_daily_sft_binding_v013588285 import diagnose

class SFTBindingTests(unittest.TestCase):
    @patch("diagnose_daily_sft_binding_v013588285.checkpoint_trained_fingerprints")
    @patch("diagnose_daily_sft_binding_v013588285.load_training_state")
    @patch("diagnose_daily_sft_binding_v013588285.deduplicate_trusted_rows")
    @patch("diagnose_daily_sft_binding_v013588285.load_chat_jsonl")
    def test_original_base_retrains_candidate_skips(self,load,dedupe,state,checkpoint):
        rows=[("おはよう","おはよう。","chat-manual")]
        load.return_value=rows;dedupe.return_value=rows
        from online_train import pair_fingerprint
        fp=pair_fingerprint("おはよう","おはよう。")
        state.return_value={fp}
        checkpoint.side_effect=[set(),{fp}]
        x=diagnose("train","state","original","candidate")
        self.assertEqual(x["retrain_if_original_base"],1)
        self.assertEqual(x["retrain_if_candidate_base"],0)
        self.assertFalse(x["production_changed"])
    @patch("diagnose_daily_sft_binding_v013588285.checkpoint_trained_fingerprints")
    @patch("diagnose_daily_sft_binding_v013588285.load_training_state")
    @patch("diagnose_daily_sft_binding_v013588285.deduplicate_trusted_rows")
    @patch("diagnose_daily_sft_binding_v013588285.load_chat_jsonl")
    def test_missing_state_retrains_even_if_checkpoint_has_pair(self,load,dedupe,state,checkpoint):
        rows=[("やあ","こんにちは","chat-manual")]
        load.return_value=rows;dedupe.return_value=rows
        from online_train import pair_fingerprint
        fp=pair_fingerprint("やあ","こんにちは")
        state.return_value=set();checkpoint.side_effect=[{fp},{fp}]
        x=diagnose("train","state","original","candidate")
        self.assertEqual(x["retrain_if_candidate_base"],1)
if __name__=="__main__":unittest.main()

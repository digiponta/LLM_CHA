import unittest
import torch
from model import LanguageModel
from checkpoint_selection_copy_v023315 import select_checkpoint_records,snapshot

class CheckpointSelectionTests(unittest.TestCase):
    def test_selects_validation_final_and_seen(self):
        rows=[{"epoch":1,"val_nll":3.5,"seen_copy_count":0},
              {"epoch":2,"val_nll":4.2,"seen_copy_count":2},
              {"epoch":3,"val_nll":4.9,"seen_copy_count":1}]
        self.assertEqual(select_checkpoint_records(rows),
          {"best_validation":1,"best_seen_copy":2,"final_epoch":3})
    def test_seen_tie_broken_by_validation(self):
        rows=[{"epoch":1,"val_nll":4.5,"seen_copy_count":2},
              {"epoch":2,"val_nll":3.9,"seen_copy_count":2}]
        self.assertEqual(select_checkpoint_records(rows)["best_seen_copy"],2)
    def test_empty_invalid(self):
        with self.assertRaises(ValueError):select_checkpoint_records([])
    def test_snapshots_are_independent(self):
        model=LanguageModel(vocab_size=32,d_model=16,num_layers=1,hidden_dim=32,
                            num_heads=4,context_length=16)
        copy=snapshot(model)
        with torch.no_grad():next(model.parameters()).add_(1.)
        self.assertFalse(torch.equal(copy[next(iter(copy))],model.state_dict()[next(iter(copy))]))
if __name__=="__main__":unittest.main()

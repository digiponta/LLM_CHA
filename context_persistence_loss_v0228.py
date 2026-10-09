"""v0.2.28 context-only phase-aware SFT loss.

All token positions are aligned targets of assistant responses (already shifted).
Context provenance is explicit per row, never inferred from question text.
"""
import torch
import torch.nn.functional as F


def persistence_loss(logits, targets, response_mask, context_flags,
                     init_k=8, init_weight=0.5, late_weight=0.5):
    if logits.ndim != 3 or targets.shape != logits.shape[:2] or response_mask.shape != targets.shape:
        raise ValueError("logits must be [B,T,V], targets/mask [B,T]")
    if context_flags.shape != (targets.shape[0],):
        raise ValueError("context_flags must be [B]")
    if not isinstance(init_k,int) or init_k < 1 or not (0 <= init_weight <= 10 and 0 <= late_weight <= 10):
        raise ValueError("invalid phase hyperparameters")
    valid = response_mask.to(logits.device).bool() & (targets.to(logits.device) != -100)
    if not valid.any().item():
        raise ValueError("no response tokens")
    masked_targets = targets.to(logits.device).masked_fill(~valid, -100)
    loss_by_token = F.cross_entropy(logits.float().reshape(-1,logits.shape[-1]),
                                    masked_targets.reshape(-1),ignore_index=-100,
                                    reduction="none").reshape_as(targets)
    base = loss_by_token.masked_select(valid).mean()
    context = valid & context_flags.to(logits.device).bool()[:,None]
    position = valid.long().cumsum(dim=1)
    initial = context & (position <= init_k)
    # Middle/late supervision excludes the first K tokens and includes remaining response.
    later = context & (position > init_k)
    def avg(mask):
        return loss_by_token.masked_select(mask).mean() if mask.any().item() else base * 0
    early_loss, later_loss = avg(initial),avg(later)
    return base + init_weight*early_loss + late_weight*later_loss, {
        "normal_loss":base.detach(),
        "init_loss":early_loss.detach(),
        "later_loss":later_loss.detach(),
        "init_tokens":int(initial.sum().item()),
        "later_tokens":int(later.sum().item()),
    }

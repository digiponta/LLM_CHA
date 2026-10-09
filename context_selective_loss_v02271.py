"""Context-selective response initiation auxiliary loss (v0.2.27.1)."""
import torch
import torch.nn.functional as F


def context_selective_loss(logits, targets, response_mask, context_flags, k=8, weight=0.5):
    if logits.ndim != 3 or targets.shape != logits.shape[:2] or response_mask.shape != targets.shape:
        raise ValueError("invalid logits/targets/mask dimensions")
    if context_flags.shape != (logits.shape[0],):
        raise ValueError("context flags must have one item per batch row")
    if not isinstance(k, int) or k < 1 or not 0 <= weight <= 10:
        raise ValueError("invalid k or weight")
    valid = response_mask.to(device=logits.device, dtype=torch.bool)
    if not valid.any().item():
        raise ValueError("empty response mask")
    target = targets.to(logits.device)
    safe = target.masked_fill(~valid, -100)
    per_token = F.cross_entropy(
        logits.float().reshape(-1, logits.size(-1)),
        safe.reshape(-1), reduction="none", ignore_index=-100,
    ).reshape_as(targets)
    normal = per_token.masked_select(valid).mean()
    selected = valid & (valid.long().cumsum(dim=1) <= k) & context_flags.to(
        device=logits.device, dtype=torch.bool
    )[:, None]
    # Batch with no context rows: exact normal loss, not NaN.
    auxiliary = per_token.masked_select(selected).mean() if selected.any().item() else normal * 0.0
    return normal + weight * auxiliary, {
        "normal_loss": normal.detach(),
        "context_initial_loss": auxiliary.detach(),
        "context_initial_tokens": int(selected.sum().item()),
    }

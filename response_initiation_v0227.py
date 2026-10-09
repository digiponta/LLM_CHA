"""LLM_CHA v0.2.27: auxiliary loss on the first K response tokens.

Inputs must be aligned/shifted causal LM logits and targets, plus an explicit
assistant-only response mask. Prompt and padding tokens must be masked out.
"""
from __future__ import annotations

import torch
import torch.nn.functional as F


def initiation_loss(logits, targets, response_mask, k=8, weight=0.5, ignore_index=-100):
    """Differentiable normal + response-initiation objective.

    logits: [batch, time, vocab] predicts targets at matching positions.
    targets: [batch, time] already aligned to logits.
    response_mask: [batch, time], 1 only at assistant answer positions.
    """
    if logits.ndim != 3 or targets.shape != logits.shape[:2] or response_mask.shape != targets.shape:
        raise ValueError("expected logits [B,T,V], targets/mask [B,T]")
    if not isinstance(k, int) or k < 1 or not (0 <= weight <= 10):
        raise ValueError("k must be positive integer; weight in [0,10]")
    mask = response_mask.to(device=logits.device, dtype=torch.bool) & (targets != ignore_index)
    if not torch.any(mask).item():
        raise ValueError("batch contains no valid response tokens")
    safe_targets = targets.to(logits.device).masked_fill(~mask, ignore_index)
    losses = F.cross_entropy(
        logits.float().reshape(-1, logits.shape[-1]),
        safe_targets.reshape(-1),
        reduction="none",
        ignore_index=ignore_index,
    ).reshape_as(targets)
    first_k = mask & (mask.long().cumsum(dim=1) <= k)
    normal = losses.masked_select(mask).mean()
    initial = losses.masked_select(first_k).mean()
    total = normal + weight * initial
    return total, {
        "normal_loss": normal.detach(),
        "initial_loss": initial.detach(),
        "initial_tokens": int(first_k.sum().item()),
        "response_tokens": int(mask.sum().item()),
    }

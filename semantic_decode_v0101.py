"""Frozen-model greedy/beam decoding; references are never used."""
from dataclasses import dataclass
import time
import torch
import torch.nn.functional as F

@dataclass
class DecodeResult:
    text: str
    token_ids: list
    score: float
    elapsed_ms: float

def _penalize(logits, response, penalty):
    if penalty < 1:
        raise ValueError("repetition penalty must be >= 1")
    logits = logits.clone()
    if penalty != 1:
        for tid in set(response):
            if 0 <= tid < logits.numel():
                logits[tid] = logits[tid] / penalty if logits[tid] >= 0 else logits[tid] * penalty
    return logits

def _score(score, length, alpha):
    return score / (((5 + max(length, 1)) / 6) ** alpha)

def decode(model, tokenizer, prompt, *, beam_width=1, max_new_tokens=32,
           repetition_penalty=1., length_penalty=1., stop_at_newline=True):
    if beam_width < 1 or max_new_tokens < 1:
        raise ValueError("beam_width and max_new_tokens must be positive")
    device = next(model.parameters()).device
    prompt_ids = tokenizer.encode(prompt, add_bos=True)
    if not prompt_ids:
        raise ValueError("empty prompt encoding")
    eos = tokenizer.eos_id
    beams = [((), 0., False)]
    model.eval()
    started = time.perf_counter()
    with torch.inference_mode():
        for _ in range(max_new_tokens):
            candidates = []
            for resp, score, finished in beams:
                if finished:
                    candidates.append((resp, score, True))
                    continue
                ids = (list(prompt_ids) + list(resp))[-model.context_length:]
                x = torch.tensor([ids], dtype=torch.long, device=device)
                logits = _penalize(model(x)[0, -1, :], resp, repetition_penalty)
                log_probs = F.log_softmax(logits, dim=-1)
                vals, idx = torch.topk(log_probs, min(beam_width, log_probs.numel()))
                for val, tid in zip(vals.tolist(), idx.tolist()):
                    if tid == eos:
                        candidates.append((resp, score + val, True))
                    else:
                        new_resp = resp + (tid,)
                        done = stop_at_newline and "\n" in tokenizer.decode(list(new_resp), skip_special_tokens=True)
                        candidates.append((new_resp, score + val, done))
            beams = sorted(candidates, key=lambda b: _score(b[1], len(b[0]), length_penalty), reverse=True)[:beam_width]
            if all(b[2] for b in beams):
                break
    best = max(beams, key=lambda b: _score(b[1], len(b[0]), length_penalty))
    output = tokenizer.decode(list(best[0]), skip_special_tokens=True).split("\n", 1)[0].strip()
    return DecodeResult(output, list(best[0]), _score(best[1], len(best[0]), length_penalty),
                        (time.perf_counter() - started) * 1000)

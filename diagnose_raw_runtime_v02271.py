"""Raw-model generation vs separately captured chat.py runtime outputs.

Raw = direct LanguageModel.generate with NO gate, retrieval, or fallback.
Runtime answers must come from actual chat.py logs; never fabricate them.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
import torch
from model import LanguageModel
from tokenizer_bpe import Tokenizer

DEFAULT_PROMPTS = [
    "宇宙探査について話を続けて",
    "カレーについて話を続けて",
    "深海探査について話を続けて",
    "陶芸について話を続けて",
    "今日は少し疲れたよ",
    "あなたは誰ですか",
]


def extract_runtime(log_text):
    """Parse You>/AI> text pairs; keeps gate/routing evidence when present."""
    rows, pending = [], None
    for line in log_text.splitlines():
        if re.match(r"^You> ", line):
            pending = line[5:].strip()
        elif re.match(r"^AI> ", line) and pending is not None:
            rows.append({"prompt": pending, "runtime_answer": line[4:].strip()})
            pending = None
    return rows


@torch.no_grad()
def run_raw(model, tokenizer, prompt, max_tokens=64, temperature=0.0):
    prefix = f"人: {prompt}\nAI: "
    tokens = tokenizer.encode(prefix, add_bos=True)
    generated = model.generate(
        tokens, max_new_tokens=max_tokens, eos_id=tokenizer.eos_id,
        temperature=temperature, repetition_penalty=1.15
    )
    response_ids = generated[len(tokens):]
    return {"raw_answer": tokenizer.decode(response_ids),
            "generated_tokens": len(response_ids)}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", required=True)
    p.add_argument("--tokenizer", default="../LLM_TRY/model/tokenizer-v0.7-bpe.json")
    p.add_argument("--prompts", help="UTF-8 newline-separated input prompts")
    p.add_argument("--runtime-log", help="Optional captured chat.py output, with You>/AI> lines")
    p.add_argument("--out", default="results/raw_runtime_v02271.jsonl")
    p.add_argument("--max-new-tokens", type=int, default=64)
    p.add_argument("--temperature", type=float, default=0.0)
    a = p.parse_args()
    if a.max_new_tokens < 1:
        p.error("--max-new-tokens must be positive")
    prompts = ([s.strip() for s in Path(a.prompts).read_text(encoding="utf-8-sig").splitlines() if s.strip()]
               if a.prompts else DEFAULT_PROMPTS)
    observed = {}
    if a.runtime_log:
        for row in extract_runtime(Path(a.runtime_log).read_text(encoding="utf-8-sig")):
            observed.setdefault(row["prompt"], []).append(row["runtime_answer"])
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model, _ = LanguageModel.load_checkpoint(a.model, device=device)
    model.eval()
    tokenizer = Tokenizer.load(a.tokenizer)
    if model.vocab_size != tokenizer.vocab_size:
        raise ValueError("model/tokenizer vocab mismatch")
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for prompt in prompts:
            raw = run_raw(model, tokenizer, prompt, a.max_new_tokens, a.temperature)
            answers = observed.get(prompt, [])
            runtime = answers.pop(0) if answers else None
            record = {"prompt": prompt, "checkpoint": a.model, **raw,
                      "runtime_answer": runtime,
                      "runtime_observed": runtime is not None,
                      "different": (raw["raw_answer"] != runtime if runtime is not None else None),
                      "raw_prompt_format": "人: {prompt}\\nAI: ",
                      "note": "Raw generation bypasses chat.py preprocessing/context/gates; these paths are not equivalent."}
            print(json.dumps(record, ensure_ascii=False))
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print("Saved:", out)


if __name__ == "__main__":
    main()

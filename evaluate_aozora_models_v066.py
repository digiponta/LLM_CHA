#!/usr/bin/env python3
"""LLM_CHA v0.6.6: paired base/Aozora checkpoint comparison (no training)."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import torch
import torch.nn.functional as F
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from train_aozora_continued_v065 import read_corpus, split_by_work

VERSION = "v0.6.6"
PROMPTS = [
    {"id": "identity", "category": "persona", "prompt": "人: あなたは誰ですか？\nAI: "},
    {"id": "personality", "category": "persona", "prompt": "人: あなたの好きなことは何ですか？\nAI: "},
    {"id": "daily", "category": "dialogue", "prompt": "人: 今日は少し疲れました。\nAI: "},
    {"id": "followup", "category": "dialogue", "prompt": "人: 本について話しましょう。\nAI: 文学には様々な作品がある。\n人: もっと詳しく。\nAI: "},
    {"id": "literature", "category": "literature", "prompt": "人: 夏目漱石の作品について教えて。\nAI: "},
]


def validate_split(rows, held):
    train, validation, chosen = split_by_work(rows, held)
    return train, validation, chosen


def token_nll(model, tokenizer, texts, device, max_tokens=20000):
    """Token-weighted mean NLL; reset context at each fragment."""
    model.eval()
    total_loss = 0.0
    total_tokens = 0
    with torch.no_grad():
        for text in texts:
            ids = tokenizer.encode(text, add_bos=True, add_eos=True)
            for start in range(0, len(ids)-1, model.context_length):
                segment = ids[start:start + model.context_length + 1]
                if len(segment) < 2:
                    continue
                x = torch.tensor([segment[:-1]], dtype=torch.long, device=device)
                y = torch.tensor([segment[1:]], dtype=torch.long, device=device)
                logits = model(x)
                nll = F.cross_entropy(logits.reshape(-1, logits.shape[-1]),
                                      y.reshape(-1), reduction="sum")
                total_loss += float(nll.item())
                total_tokens += y.numel()
                if max_tokens and total_tokens >= max_tokens:
                    return total_loss/total_tokens, total_tokens
    if not total_tokens:
        raise ValueError("no evaluation tokens")
    return total_loss/total_tokens, total_tokens


def generate_samples(model, tokenizer, max_new_tokens):
    samples = []
    for item in PROMPTS:
        tokens = tokenizer.encode(item["prompt"])
        if not tokens:
            raise ValueError("prompt has zero tokens")
        out = model.generate(tokens, max_new_tokens=max_new_tokens,
                             temperature=0, top_k=None, repetition_penalty=1.0,
                             eos_id=tokenizer.eos_id)
        samples.append({**item, "answer": tokenizer.decode(out[len(tokens):])})
    return samples


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--baseline", default="model/model-llm-try-nagato-chat-v94.pt")
    ap.add_argument("--aozora-model", default="model/model-llm-cha-aozora-v065.pt")
    ap.add_argument("--tokenizer", default="model/tokenizer-v0.7-bpe.json")
    ap.add_argument("--corpus", default="data/aozora_v064/aozora_semantic_corpus.jsonl")
    ap.add_argument("--validation-work", default="1567")
    ap.add_argument("--output", default="results/aozora_comparison_v066.json")
    ap.add_argument("--max-eval-tokens", type=int, default=20000)
    ap.add_argument("--max-new-tokens", type=int, default=64)
    args = ap.parse_args()
    if args.max_eval_tokens < 1 or args.max_new_tokens < 1:
        ap.error("token limits must be positive")
    paths = [Path(args.baseline).resolve(), Path(args.aozora_model).resolve(), Path(args.output).resolve()]
    if len(set(paths)) != 3:
        ap.error("checkpoints and report must use distinct paths")
    if Path(args.output).exists():
        raise FileExistsError(args.output)
    rows = read_corpus(args.corpus)
    train, held_texts, held = validate_split(rows, args.validation_work)
    tokenizer = Tokenizer.load(args.tokenizer)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    result = {"version": VERSION, "device": str(device), "heldout_work": held,
              "generation_mode": "deterministic_greedy_raw_model",
              "persona_regression_verified": False,
              "note": "Raw model outputs do not exercise chat.py routing or Truth Gate.",
              "models": {}}
    for name, checkpoint_path in [("baseline", args.baseline), ("aozora", args.aozora_model)]:
        model, _ = LanguageModel.load_checkpoint(checkpoint_path, device=device)
        if model.vocab_size != tokenizer.vocab_size:
            raise ValueError("vocabulary mismatch for " + name)
        held_loss, count = token_nll(model, tokenizer, held_texts, device, args.max_eval_tokens)
        train_loss, train_count = token_nll(model, tokenizer, train, device, args.max_eval_tokens)
        result["models"][name] = {
            "checkpoint": checkpoint_path,
            "heldout_mean_nll": held_loss, "heldout_tokens_scored": count,
            "train_sample_mean_nll": train_loss, "train_tokens_scored": train_count,
            "prompts": generate_samples(model, tokenizer, args.max_new_tokens)
        }
        print(f"{name}: holdout NLL={held_loss:.5f} train-sample NLL={train_loss:.5f}")
        del model
        if device.type == "cuda":
            torch.cuda.empty_cache()
    base = result["models"]["baseline"]["heldout_mean_nll"]
    improved = result["models"]["aozora"]["heldout_mean_nll"]
    result["heldout_nll_change"] = improved-base
    result["heldout_relative_improvement_percent"] = 100*(base-improved)/base
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print("Saved:", path)
    print("Review persona/dialogue samples manually before any model promotion.")


if __name__ == "__main__":
    main()

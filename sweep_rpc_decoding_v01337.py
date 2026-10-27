"""v0.13.37 read-only seeded RPC decoding sweep."""
import argparse
import json
import random
import re
from pathlib import Path

SETTINGS = {
    "GREEDY": (0.0, 20, 1.0),
    "SAMPLE_T07": (0.7, 20, 1.0),
    "SAMPLE_T07_R12": (0.7, 20, 1.2),
    "SAMPLE_T04_R115": (0.4, 10, 1.15),
}

def repetition(text):
    s = re.sub(r"\s+", "", text)
    grams = [s[i:i+3] for i in range(max(0, len(s)-2))]
    return (len(grams)-len(set(grams)))/len(grams) if grams else 0.0

def generic(text):
    s = re.sub(r"[\s。!！?？、]+", "", text)
    return s in {"そうですね", "そうなんですね", "そうですよね", "そうですか", "そうです", "なるほど"}

def choose_probes(rows, limit, seed=1335):
    groups = {}
    for r in rows:
        groups.setdefault(str(r["dialogue_id"]), []).append(r)
    rng = random.Random(seed)
    keys = sorted(groups)
    rng.shuffle(keys)
    selected = [groups[k][len(groups[k])//2] for k in keys[:limit]]
    if len(selected) < limit:
        seen = {(str(r["dialogue_id"]), r["utterance_id"]) for r in selected}
        rest = [r for r in rows if (str(r["dialogue_id"]), r["utterance_id"]) not in seen]
        rng.shuffle(rest)
        selected.extend(rest[:limit-len(selected)])
    return selected

def summarize(rows):
    n = len(rows)
    return {
        "cases": n,
        "exact_match": sum(x["exact_match"] for x in rows),
        "mean_repetition": sum(x["repetition"] for x in rows)/n if n else None,
        "mean_tokens": sum(x["generated_tokens"] for x in rows)/n if n else None,
        "generic_reply": sum(x["generic_reply"] for x in rows),
        "empty": sum(not x["text"].strip() for x in rows),
        "hit_max_tokens": sum(x["hit_max_tokens"] for x in rows),
    }

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", type=Path, default=Path("results/rpc_sweep_v01336/rpc_candidate_100000.pt"))
    p.add_argument("--data", type=Path, default=Path("results/rpc_sft_full_v01333/rpc_sft_val_v01333.jsonl"))
    p.add_argument("--tokenizer", type=Path, default=Path("../LLM_GPU/model/tokenizer-v0.7-bpe.json"))
    p.add_argument("--output", type=Path, default=Path("results/rpc_decoding_sweep_v01337.json"))
    p.add_argument("--limit", type=int, default=24)
    p.add_argument("--max-new-tokens", type=int, default=64)
    p.add_argument("--seed", type=int, default=1337)
    a = p.parse_args()
    if a.limit < 1 or a.max_new_tokens < 1:
        p.error("limits must be positive")
    for f in (a.model, a.data, a.tokenizer):
        if not f.exists():
            p.error(f"missing {f}")
    if a.output.exists():
        p.error("output exists; choose a new filename")
    import torch
    from chat import generate_reply
    from model import LanguageModel
    from tokenizer_bpe import Tokenizer
    from online_train import USER_PREFIX, AI_PREFIX
    from train_rpc_dialogue_sft_v01334 import read_rows
    rows = choose_probes(read_rows(a.data), a.limit)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer = Tokenizer.load(str(a.tokenizer))
    model, _ = LanguageModel.load_checkpoint(str(a.model), device=device)
    model.eval()
    summary, details = {}, {}
    with torch.no_grad():
        for setting, (temp, top_k, penalty) in SETTINGS.items():
            generated = []
            for i, r in enumerate(rows):
                prompt = f"{USER_PREFIX}{r['user']}\n{AI_PREFIX}"
                result = generate_reply(model, tokenizer, prompt, a.max_new_tokens,
                                        temp, top_k, penalty, seed=a.seed+i)
                reply = result.text
                generated.append({
                    "dialogue_id": r["dialogue_id"], "utterance_id": r["utterance_id"],
                    "prompt": r["user"], "reference": r["assistant"], "text": reply,
                    "generated_tokens": result.token_count,
                    "exact_match": reply.strip() == r["assistant"].strip(),
                    "repetition": repetition(reply), "generic_reply": generic(reply),
                    "hit_max_tokens": result.token_count >= a.max_new_tokens,
                })
            details[setting] = generated
            summary[setting] = summarize(generated)
    report = {
        "version": "v0.13.37", "split": "VALIDATION", "model": str(a.model),
        "seed": a.seed,
        "settings": {k: {"temperature": v[0], "top_k": v[1], "repetition_penalty": v[2]}
                     for k, v in SETTINGS.items()},
        "summary": summary, "details": details, "production_unchanged": True,
        "caveats": [
            "GenerationResult lacks EOS termination reason; hit_max_tokens is only a length-limit indicator.",
            "Heuristic metrics do not measure semantic relevance.",
            "Use multiple seeds and human evaluation before selecting settings.",
        ],
    }
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("report:", a.output)

if __name__ == "__main__":
    main()

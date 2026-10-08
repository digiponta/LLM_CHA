"""Build leakage-controlled replay mixture for LLM_CHA v0.2.1.

Inputs: RealPersonaChat train split + manually trusted identity/response anchors.
Outputs: new train/validation JSONL; leaves all original data untouched.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import random
from pathlib import Path

DEFAULT_ANCHORS = [
    ("あなたは誰ですか", "長門有希。"),
    ("名前を教えてください", "長門有希。"),
    ("自己紹介してください", "長門有希。"),
    ("こんにちは", "こんにちは。"),
    ("ありがとう", "どういたしまして。"),
    ("今日は少し疲れました", "そう。無理せず休むといい。"),
    ("何か面白い話をして", "宇宙には、まだ解明されていない現象が多くある。"),
    ("最近は本を読んでいます", "そう。どんな本を読んでいるの？"),
    ("どんな本が好き？", "科学や数学に関する本が好き。"),
]
def read_pairs(path: Path):
    if not path.is_file():
        raise FileNotFoundError(path)
    result = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip(): continue
        row = json.loads(line)
        user, answer = row.get("user"), row.get("assistant")
        if isinstance(user,str) and isinstance(answer,str) and user.strip() and answer.strip():
            result.append({"user":user.strip(), "assistant":answer.strip()})
    return result

def write_pairs(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row,ensure_ascii=False)+"\n")

def build(source: Path, output: Path, max_rpc: int, replay_factor: int, seed: int):
    if max_rpc < 1 or replay_factor < 1: raise ValueError("positive max_rpc and replay_factor required")
    rpc = read_pairs(source)
    if not rpc: raise ValueError("No RealPersonaChat rows")
    rng = random.Random(seed)
    rpc = rng.sample(rpc, min(max_rpc,len(rpc)))
    anchors = [{"user":u,"assistant":a} for u,a in DEFAULT_ANCHORS]
    # Discard potential exact-question overlap from RPC to avoid conflicting labels.
    protected = {x["user"] for x in anchors}
    rpc = [x for x in rpc if x["user"] not in protected]
    train = rpc + anchors * replay_factor
    rng.shuffle(train)
    output.mkdir(parents=True, exist_ok=True)
    write_pairs(output/"rpc_replay_train.jsonl",train)
    write_pairs(output/"rpc_replay_anchor_eval.jsonl",anchors)
    report = {"rpc_rows":len(rpc),"anchor_unique":len(anchors),"anchor_repetitions":replay_factor,
              "training_rows":len(train),"seed":seed,"note":"Anchor evaluation is a retention diagnostic, not an independent held-out score"}
    (output/"rpc_replay_manifest.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return report

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source",type=Path,default=Path("data/realpersonachat/rpc_train.jsonl"))
    parser.add_argument("--output",type=Path,default=Path("data/realpersonachat_replay"))
    parser.add_argument("--max-rpc",type=int,default=20000)
    parser.add_argument("--replay-factor",type=int,default=300)
    parser.add_argument("--seed",type=int,default=42)
    args=parser.parse_args()
    print(json.dumps(build(args.source,args.output,args.max_rpc,args.replay_factor,args.seed),ensure_ascii=False,indent=2))
if __name__ == "__main__": main()

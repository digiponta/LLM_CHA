"""v0.2.27: paired ordinary SFT vs initiation-weighted SFT experiment."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from train_context_weighted_v0224 import command


def build_command(args):
    cmd, stats = command(args)
    assert Path(cmd[1]).name == "train_nagato_chat.py", "Upstream trainer changed"
    cmd[1] = "train_response_initiation_v0227.py"
    cmd.extend(["--init-k", str(args.init_k), "--init-weight", str(args.init_weight)])
    return cmd, stats


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--train", default="data/context_generalization_v0225/train.jsonl")
    p.add_argument("--context", default="data/context_generalization_v0225/context.jsonl")
    p.add_argument("--val", default="data/context_generalization_v0225/val.jsonl")
    p.add_argument("--manifest", default="data/context_generalization_v0225/manifest.json")
    p.add_argument("--anchors", default="data/realpersonachat_quality/persona_anchors_preformatted.jsonl")
    p.add_argument("--base-model", default="model/model-llm-cha-response-quality-v0221.pt")
    p.add_argument("--tokenizer", default="../LLM_TRY/model/tokenizer-v0.7-bpe.json")
    p.add_argument("--output", default="")
    p.add_argument("--context-weight", type=int, default=12)
    p.add_argument("--anchor-weight", type=int, default=10)
    p.add_argument("--epochs", type=int, default=3)
    p.add_argument("--batch-size", type=int, default=8)
    p.add_argument("--learning-rate", type=float, default=2e-6)
    p.add_argument("--lm-head-learning-rate", type=float, default=3e-7)
    p.add_argument("--init-k", type=int, default=8)
    p.add_argument("--init-weight", type=float, default=0.0)
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args()
    if not a.output:
        suffix = f"k{a.init_k}-w{str(a.init_weight).replace('.', 'p')}"
        a.output = f"model/model-llm-cha-init-v0227-{suffix}.pt"
    if min(a.epochs, a.batch_size, a.context_weight, a.anchor_weight, a.init_k) < 1:
        p.error("Positive values required for epochs, batch, context/anchor weights and K.")
    if not 0 <= a.init_weight <= 10:
        p.error("init-weight must be between 0 and 10")
    cmd, stats = build_command(a)
    print("Training exposures:", json.dumps(stats, ensure_ascii=False), flush=True)
    print("Command:", subprocess.list2cmdline(cmd), flush=True)
    if not a.dry_run:
        subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()

"""Train an isolated RealPersonaChat general-dialogue checkpoint.

Uses the existing LLM_CHA assistant-only SFT implementation, never overwrites
the input checkpoint, and never writes to Semantic Memory or persona profiles.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import subprocess
import sys

def build_command(args):
    output = Path(args.output)
    base = Path(args.base_model)
    if not base.exists():
        raise FileNotFoundError(f"Base checkpoint missing: {base}")
    if base.resolve() == output.resolve():
        raise ValueError("Output must differ from base checkpoint")
    for path in (args.tokenizer, args.train, args.val):
        if not Path(path).is_file():
            raise FileNotFoundError(f"Required input missing: {path}")
    return [
        sys.executable, "train_nagato_chat.py",
        "--data", args.train, "--val-data", args.val,
        "--tokenizer", args.tokenizer, "--base-model", args.base_model,
        "--output", args.output, "--epochs", str(args.epochs),
        "--batch-size", str(args.batch_size),
        "--learning-rate", str(args.learning_rate),
        "--lm-head-learning-rate", str(args.lm_head_learning_rate),
        "--trainable-blocks", str(args.trainable_blocks),
        "--repeat", "1",
        "--canonical-identity-weight", "1",
        "--canonical-persona-weight", "1",
        "--canonical-knowledge-weight", "1",
        "--canonical-paraphrase-weight", "1",
        "--persona-weight", "1",
    ]

def main():
    parser = argparse.ArgumentParser(description="RealPersonaChat general conversation SFT")
    parser.add_argument("--train", default="data/realpersonachat/rpc_train.jsonl")
    parser.add_argument("--val", default="data/realpersonachat/rpc_val.jsonl")
    parser.add_argument("--tokenizer", default="model/tokenizer-v0.7-bpe.json")
    parser.add_argument("--base-model", default="model/model-llm-try-nagato-chat-v94.pt")
    parser.add_argument("--output", default="model/model-llm-cha-rpc-v020.pt")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--learning-rate", type=float, default=5e-6)
    parser.add_argument("--lm-head-learning-rate", type=float, default=1e-6)
    parser.add_argument("--trainable-blocks", type=int, default=2)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.epochs < 1 or args.batch_size < 1:
        parser.error("epochs and batch-size must be positive")
    cmd = build_command(args)
    print("Command:", subprocess.list2cmdline(cmd), flush=True)
    if not args.dry_run:
        subprocess.run(cmd, check=True)

if __name__ == "__main__":
    main()

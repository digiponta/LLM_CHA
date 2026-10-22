#!/usr/bin/env python3
"""LLM_CHA v0.6.5 — guarded GPU continued pretraining on Aozora Bunko.

Hold out entire works to prevent cross-chunk leakage. Saves a NEW checkpoint.
Literature is not promoted as factual Semantic Memory.
"""
import argparse
import hashlib
import json
import math
import random
from pathlib import Path

import torch
from torch.utils.data import DataLoader

from model import LanguageModel
from tokenizer_bpe import Tokenizer
from train_nagato_full import FullCorpusDataset, evaluate, lm_loss

VERSION = "v0.6.5"


def read_corpus(path):
    rows = []
    for i, raw in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        r = json.loads(raw)
        p = r.get("provenance", {})
        work = str(p.get("work_id", ""))
        txt = r.get("text", "")
        if (not work or not isinstance(txt, str) or not txt.strip()
                or r.get("train_ready") is not False
                or r.get("auto_promote") is not False
                or not isinstance(r.get("natural_language_refs"), list)
                or not r["natural_language_refs"]):
            raise ValueError(f"invalid corpus row {i}")
        ref = r["natural_language_refs"][0]
        expected = "sha256:" + hashlib.sha256(txt.encode("utf-8")).hexdigest()
        if ref.get("content_hash") != expected:
            raise ValueError(f"content hash mismatch at row {i}")
        rows.append((work, txt))
    return rows


def split_by_work(rows, validation_work=None):
    works = sorted({work for work, _ in rows})
    if len(works) < 2:
        raise ValueError("need at least two distinct works for independent validation")
    held = str(validation_work) if validation_work is not None else works[0]
    if held not in works:
        raise ValueError("validation work not found")
    train = [text for work, text in rows if work != held]
    val = [text for work, text in rows if work == held]
    if not train or not val:
        raise ValueError("empty split")
    return train, val, held


def make_dataset(texts, tokenizer, block, stride):
    # Separate fragments by EOS; never join unseparated works.
    ids = []
    for text in texts:
        ids.extend(tokenizer.encode(text, add_bos=True, add_eos=True))
    return FullCorpusDataset(ids, block_size=block, stride=stride), len(ids)


def path_guard(base, output, report):
    b, o, r = (Path(x).resolve() for x in (base, output, report))
    if len({b, o, r}) != 3:
        raise ValueError("base checkpoint, output checkpoint and report must differ")
    if o.exists():
        raise FileExistsError(f"output checkpoint already exists: {o}")
    if r.exists():
        raise FileExistsError(f"report already exists: {r}")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--corpus", default="data/aozora_v064/aozora_semantic_corpus.jsonl")
    p.add_argument("--tokenizer", default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--base-model", default="model/model-llm-try-nagato-chat-v94.pt")
    p.add_argument("--output", default="model/model-llm-cha-aozora-v065.pt")
    p.add_argument("--report", default="results/aozora_training_v065.json")
    p.add_argument("--validation-work", default="1567")
    p.add_argument("--epochs", type=int, default=2)
    p.add_argument("--batch-size", type=int, default=4)
    p.add_argument("--block-size", type=int, default=128)
    p.add_argument("--learning-rate", type=float, default=5e-6)
    p.add_argument("--max-steps-per-epoch", type=int, default=0,
                   help="0 for all training windows")
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args()
    if a.epochs < 1 or a.batch_size < 1 or a.block_size < 8 or a.learning_rate <= 0 or a.max_steps_per_epoch < 0:
        p.error("invalid training parameters")
    path_guard(a.base_model, a.output, a.report)
    random.seed(42)
    torch.manual_seed(42)
    rows = read_corpus(a.corpus)
    train, validation, held = split_by_work(rows, a.validation_work)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tok = Tokenizer.load(a.tokenizer)
    model, base_ckpt = LanguageModel.load_checkpoint(a.base_model, device=device)
    if tok.vocab_size != model.vocab_size:
        raise ValueError("tokenizer/model vocabulary mismatch")
    block = min(a.block_size, model.context_length)
    train_ds, train_tokens = make_dataset(train, tok, block, block)
    val_ds, val_tokens = make_dataset(validation, tok, block, block)
    print(f"device={device} holdout_work={held} train_tokens={train_tokens} validation_tokens={val_tokens}")
    print(f"train_windows={len(train_ds)} val_windows={len(val_ds)} checkpoint={a.base_model}")
    if a.dry_run:
        print("DRY RUN: no weights modified or files written")
        return
    train_loader = DataLoader(train_ds, batch_size=a.batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=a.batch_size)
    train_eval = DataLoader(train_ds, batch_size=a.batch_size)
    optimizer = torch.optim.AdamW(model.parameters(), lr=a.learning_rate, weight_decay=0.01)
    before_train, _ = evaluate(model, train_eval, device)
    before_val, _ = evaluate(model, val_loader, device)
    epoch_reports = []
    for epoch in range(1, a.epochs + 1):
        model.train()
        losses = []
        for step, (x, y) in enumerate(train_loader, 1):
            if a.max_steps_per_epoch and step > a.max_steps_per_epoch:
                break
            x, y = x.to(device), y.to(device)
            optimizer.zero_grad(set_to_none=True)
            loss = lm_loss(model, x, y)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            losses.append(float(loss.item()))
            if step == 1 or step % 10 == 0:
                print(f"epoch={epoch}/{a.epochs} step={step}/{len(train_loader)} loss={loss.item():.5f}")
        after_val, _ = evaluate(model, val_loader, device)
        epoch_reports.append({"epoch": epoch, "train_step_loss": sum(losses)/len(losses), "validation_loss": after_val})
        print(f"epoch={epoch} heldout_loss={after_val:.5f}")
    after_train, _ = evaluate(model, train_eval, device)
    after_val, _ = evaluate(model, val_loader, device)
    report = {
        "version": VERSION, "validation_work": held, "train_tokens": train_tokens,
        "validation_tokens": val_tokens, "train_windows": len(train_ds),
        "validation_windows": len(val_ds), "before_train_loss": before_train,
        "after_train_loss": after_train, "before_validation_loss": before_val,
        "after_validation_loss": after_val, "epochs": epoch_reports,
        "base_model": a.base_model, "output_model": a.output,
        "semantic_memory_modified": False, "persona_regression_verified": False
    }
    # Never overwrite the input checkpoint or a previous output checkpoint.
    out = Path(a.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists(): raise FileExistsError(out)
    model.save_checkpoint(str(out), optimizer=optimizer, epoch=a.epochs,
                          loss=after_val, metadata={"training": VERSION, "holdout_work": held})
    report_path = Path(a.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

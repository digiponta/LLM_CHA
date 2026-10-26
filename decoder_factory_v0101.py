"""Load a frozen LLM_CHA checkpoint for decoder comparisons.

Set LLM_CHA_DECODE_MODEL to the EXACT v0.10.0 evaluated checkpoint to
preserve comparability. No checkpoint is written or training invoked.
"""
import os
from pathlib import Path
import torch
from model import LanguageModel
from tokenizer_bpe import Tokenizer

def load():
    model_arg = os.environ.get("LLM_CHA_DECODE_MODEL")
    tokenizer_arg = os.environ.get("LLM_CHA_DECODE_TOKENIZER", r"C:\Users\inoma\git\misc\LLM_GPU\model\tokenizer-v0.7-bpe.json")
    if not model_arg:
        raise RuntimeError("Set LLM_CHA_DECODE_MODEL to the checkpoint used in v0.10.0.")
    model_path = Path(model_arg).expanduser().resolve(strict=True)
    tokenizer_path = Path(tokenizer_arg).expanduser().resolve(strict=True)
    if model_path.suffix.lower() != ".pt":
        raise ValueError("Expected .pt checkpoint")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model, checkpoint = LanguageModel.load_checkpoint(str(model_path), device)
    tokenizer = Tokenizer.load(str(tokenizer_path))
    vocab = tokenizer.backend.get_vocab_size()
    if int(model.vocab_size) != int(vocab):
        raise ValueError(f"Tokenizer/model vocab mismatch: {vocab} != {model.vocab_size}")
    model.eval()
    for p in model.parameters():
        p.requires_grad_(False)
    print(f"[decode-factory] checkpoint={model_path} tokenizer={tokenizer_path} device={device} vocab={vocab}")
    return model, tokenizer

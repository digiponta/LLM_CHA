"""Read-only startup preflight for an isolated LLM_CHA chat benchmark.

No model is loaded. Check only file accessibility and import availability.
"""
import importlib.util
import sys
from pathlib import Path

REQUIRED_ASSETS=(
    "model/model-llm-try-nagato-chat-v94.pt",
    "model/tokenizer-v0.7-bpe.json",
    "data/data-nagato.txt",
)
REQUIRED_MODULES=("torch",)

def preflight(root):
    root=Path(root)
    entries=[]
    for rel in REQUIRED_ASSETS:
        item=root/rel
        # Default chat.py may also resolve models from ../LLM_GPU.
        alt=root.parent/"LLM_GPU"/rel if rel.startswith("model/") else None
        located=item if item.is_file() else (alt if alt is not None and alt.is_file() else None)
        entries.append({"kind":"file","name":rel,
                        "ok":located is not None,
                        "location":str(located) if located else None})
    for name in REQUIRED_MODULES:
        entries.append({"kind":"python_module","name":name,
                        "ok":importlib.util.find_spec(name) is not None})
    entries.append({"kind":"python","name":sys.executable,
                    "ok":bool(sys.executable)})
    return {"ok":all(entry["ok"] for entry in entries),"checks":entries,
            "note":"Read-only heuristic: success does not guarantee chat.py initializes."}

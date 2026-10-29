"""Side-effect-free local status snapshot for both CLI and GUI."""
from pathlib import Path
import json

def get_status(root=None):
    root=Path(root or Path(__file__).resolve().parent)
    approval=root/"data"/"independently_approved_sources.json"
    approved=0
    if approval.is_file():
        try:
            payload=json.loads(approval.read_text(encoding="utf-8-sig"))
            if isinstance(payload.get("approved_source_ids"),list):
                approved=len(payload["approved_source_ids"])
        except (ValueError,OSError,AttributeError):pass
    return {
        "version":"v0.13.58.82",
        "cli":"chat.py",
        "gui":"chat_gui.py",
        "retrieval":"experimental / offline only",
        "verifier":"v0.13.58.81 experimental; runtime auto-accept DISABLED",
        "approval_source_file":str(approval),
        "approved_source_count":approved,
        "model_present":(root/"model"/"model-llm-try-nagato-chat-v94.pt").is_file(),
        "tokenizer_present":(root/"model"/"tokenizer-v0.7-bpe.json").is_file(),
    }

def status_text(root=None):
    info=get_status(root)
    return "[LLM_CHA status]\n"+ "\n".join(f"  {k}: {v}" for k,v in info.items())

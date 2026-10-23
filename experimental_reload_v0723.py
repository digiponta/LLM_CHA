"""v0.7.23 verified Experimental checkpoint hot reload after /sleep."""
from pathlib import Path

def validated_backend(checkpoint_path, base_path, tokenizer_path, pending_ids,
                      *,backend_class=None):
    import torch
    from experimental_backend_v0711 import ExperimentalBackend
    path=Path(checkpoint_path)
    if not path.is_file():
        raise FileNotFoundError(path)
    ckpt=torch.load(path,map_location="cpu",weights_only=True)
    if ckpt.get("route")!="experimental" or ckpt.get("approved") is not False:
        raise ValueError("not an experimental-only checkpoint")
    ids=ckpt.get("candidate_ids")
    if not isinstance(ids,(list,tuple)) or set(ids)!=set(pending_ids):
        raise ValueError("checkpoint does not match current PENDING candidate IDs")
    if len(ids)!=len(pending_ids):
        raise ValueError("duplicate checkpoint candidate IDs")
    if not isinstance(ckpt.get("rank"),int) or ckpt["rank"]<1:
        raise ValueError("invalid adapter rank")
    if "base_hash" not in ckpt or "adapter" not in ckpt:
        raise ValueError("missing base hash or adapter tensors")
    cls=backend_class or ExperimentalBackend
    backend=cls(base_path,tokenizer_path,path)
    # Force checkpoint validation, including Base identity and tensor shape,
    # before replacing an existing inference backend.
    backend("動作確認")
    return backend

def reload_after_sleep(result,approved_path,candidate_path,base_path,
                       tokenizer_path,old_backend,*,backend_class=None):
    if result.get("status") not in {"TRAINED","ALREADY_TRAINED"}:
        return old_backend,{"status":"UNCHANGED","reason":"no_training"}
    from dual_semantic_memory_v071 import DualMemory
    memory=DualMemory(approved_path,candidate_path)
    pending=[r["id"] for r in memory.candidates() if r["status"]=="PENDING"]
    try:
        backend=validated_backend(result["checkpoint"],base_path,tokenizer_path,
                                  pending,backend_class=backend_class)
    except Exception as exc:  # Invalid checkpoint or backend initialization: fail closed.
        return old_backend,{"status":"REJECTED","reason":type(exc).__name__}
    return backend,{"status":"LOADED","checkpoint":result["checkpoint"],
                    "candidate_count":len(pending),"trusted_changed":False}

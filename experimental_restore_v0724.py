"""v0.7.24: restore matching experimental sleep checkpoint on startup."""
from pathlib import Path
from experimental_reload_v0723 import validated_backend

def restore_latest(folder, approved_path, candidate_path, base_path, tokenizer_path,
                   *, backend_class=None):
    from dual_semantic_memory_v071 import DualMemory
    pending=[r["id"] for r in DualMemory(approved_path,candidate_path).candidates()
             if r["status"]=="PENDING"]
    if not pending:
        return None,{"status":"NO_PENDING","checked":0}
    paths=sorted(Path(folder).glob("experimental-sleep-*.pt"),
                 key=lambda p:(p.stat().st_mtime_ns,p.name),reverse=True)
    if not paths:
        return None,{"status":"NO_CHECKPOINT","checked":0}
    failures=[]
    for path in paths:
        try:
            backend=validated_backend(path,base_path,tokenizer_path,pending,
                                       backend_class=backend_class)
            return backend,{"status":"RESTORED","checkpoint":str(path),
                            "checked":len(failures)+1,
                            "candidate_count":len(pending)}
        except Exception as exc:
            failures.append({"file":path.name,"reason":type(exc).__name__})
    return None,{"status":"NO_VALID_CHECKPOINT","checked":len(failures),
                 "failures":failures}

"""v0.7.22 Experimental-only /sleep training.

Trains only the Experimental Adapter with PENDING Candidate Memory.
Never uses the Trusted checkpoint as output or promotes Candidate records.
"""
import hashlib
import json
from pathlib import Path
from dual_semantic_memory_v071 import DualMemory

def experimental_sleep(approved_path,candidate_path,base_path,tokenizer_path,output_dir,
                       *,rank=16,epochs=30,lr=1e-3,trainer=None):
    memory=DualMemory(approved_path,candidate_path)
    pending=[r for r in memory.candidates() if r["status"]=="PENDING"]
    if not pending:
        return {"status":"NO_PENDING","pending":0,"trained":False,
                "trusted_changed":False,"auto_promote":False}
    # Deterministic snapshot key: same candidate identities, source, answers,
    # training settings and base identity yield the same immutable checkpoint.
    config={"records":[[r["id"],r["question"],r["answer"],r["source_id"]]
                       for r in sorted(pending,key=lambda x:x["id"])],
            "base":str(Path(base_path).resolve()),
            "tokenizer":str(Path(tokenizer_path).resolve()),
            "rank":rank,"epochs":epochs,"lr":lr}
    digest=hashlib.sha256(json.dumps(config,ensure_ascii=False,sort_keys=True).encode("utf-8")).hexdigest()[:20]
    destination=Path(output_dir)/("experimental-sleep-"+digest+".pt")
    if destination.exists():
        import torch
        ckpt=torch.load(destination,map_location="cpu",weights_only=True)
        if ckpt.get("candidate_ids")!=[r["id"] for r in pending]:
            # Matching snapshot but differing serialization order is harmless
            if set(ckpt.get("candidate_ids",[]))!={r["id"] for r in pending}:
                raise ValueError("existing experimental checkpoint candidate mismatch")
        if ckpt.get("route")!="experimental" or ckpt.get("approved") is not False:
            raise ValueError("existing checkpoint is not experimental-only")
        return {"status":"ALREADY_TRAINED","pending":len(pending),"trained":False,
                "checkpoint":str(destination),"trusted_changed":False,"auto_promote":False}
    if trainer is None:
        from train_experimental_adapter_v073 import run as trainer
    result=trainer(base_path,tokenizer_path,approved_path,candidate_path,destination,
                   rank=rank,epochs=epochs,lr=lr)
    return {"status":"TRAINED","pending":len(pending),"trained":True,
            "checkpoint":str(destination),"training":result,
            "trusted_changed":False,"auto_promote":False}

"""v0.8.0.15: isolated /sleep weight training for unapproved Wikipedia facts.

The original model and trusted adapter stay frozen. Only an experimental
adapter checkpoint is written. Training is NOT factual approval.
"""
import hashlib
import json
from pathlib import Path
from unapproved_llm_intake_v074446 import DEFAULT_STORE, _read

def eligible_candidates(store=DEFAULT_STORE):
    candidates=_read(store)["candidates"]
    return sorted([r for r in candidates
       if r.get("state")=="UNAPPROVED"
       and r.get("truth_state")=="EXTERNAL_UNVERIFIED"
       and r.get("source_type","Wikipedia")=="Wikipedia"
       and str(r.get("source","")).startswith("https://ja.wikipedia.org/")
       and not r.get("suspected_conflicts")
       and (r.get("semantic_candidate") or {}).get("status")=="STRUCTURED"
       and r.get("id") and r.get("subject") and r.get("natural_language")],
       key=lambda r:r["id"])

def sleep_unapproved_wikipedia(
        store=DEFAULT_STORE, base="model/model-gpu-v1.6.2-online.pt",
        tokenizer_path="model/tokenizer-v0.7-bpe.json",
        output_dir="results/unapproved_wiki_sleep_v08015",
        rank=8, epochs=3, lr=1e-4, trainer=None):
    rows=eligible_candidates(store)
    if not rows:
        return {"status":"NO_ELIGIBLE","eligible":0,"trained":False,
                "trusted_changed":False,"approved":False}
    base=Path(base).resolve()
    tokenizer_path=Path(tokenizer_path).resolve()
    store=Path(store).resolve()
    output_dir=Path(output_dir).resolve()
    config={"records":[[r["id"],r["subject"],r["natural_language"],
                        r["source"],r["semantic_candidate"]] for r in rows],
            "base":str(base),"tokenizer":str(tokenizer_path),
            "rank":rank,"epochs":epochs,"lr":lr,
            "version":"v0.8.0.15"}
    # Snapshot hash is stable for unchanged data and parameters.
    digest=hashlib.sha256(json.dumps(config,ensure_ascii=False,sort_keys=True).encode("utf-8")).hexdigest()[:20]
    dest=output_dir/("unapproved-wiki-adapter-"+digest+".pt")
    if dest.exists():
        # Do not import torch unnecessarily for no-op checks.
        import torch
        ck=torch.load(dest,map_location="cpu",weights_only=True)
        if ck.get("route")!="unapproved_wikipedia" or ck.get("approved") is not False:
            raise ValueError("invalid unapproved checkpoint")
        if ck.get("candidate_ids")!=[r["id"] for r in rows]:
            raise ValueError("checkpoint candidate mismatch")
        return {"status":"ALREADY_TRAINED","eligible":len(rows),
                "trained":False,"checkpoint":str(dest),
                "trusted_changed":False,"approved":False}
    if trainer is None:
        trainer=train_unapproved_adapter
    result=trainer(rows,base,tokenizer_path,dest,rank,epochs,lr)
    return {"status":"TRAINED","eligible":len(rows),"trained":True,
            "checkpoint":str(dest),"training":result,
            "trusted_changed":False,"approved":False}

def train_unapproved_adapter(rows,base,tokenizer_path,dest,rank,epochs,lr):
    import torch
    from model import LanguageModel
    from tokenizer_bpe import Tokenizer
    from online_train import ConversationDataset
    from dual_adapters_v073 import DualAdapterModel,frozen_digest,masked_cross_entropy
    from candidate_sandbox_train_v072 import digest as file_digest
    if epochs<1 or rank<1 or lr<=0:raise ValueError("invalid training parameters")
    if not base.is_file() or not tokenizer_path.is_file():
        raise FileNotFoundError("base model or tokenizer missing")
    if dest in (base,tokenizer_path):
        raise ValueError("checkpoint overlaps protected data")
    before={str(p):file_digest(p) for p in (base,tokenizer_path)}
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    original,_=LanguageModel.load_checkpoint(str(base),device=device)
    tokenizer=Tokenizer.load(str(tokenizer_path))
    if original.vocab_size!=tokenizer.vocab_size:
        raise ValueError("tokenizer/model vocab mismatch")
    model=DualAdapterModel(original,rank=rank).to(device)
    original_digest=frozen_digest(original)
    trusted=model.export_adapter("trusted")
    # Evidence questions are explicitly source-scoped; the model is not
    # trained to present unverified Wikipedia sentences as established truth.
    pairs=[(r["subject"]+"についてWikipediaの未検証情報は？",
            "Wikipediaの未検証情報: "+r["natural_language"])
           for r in rows]
    data=ConversationDataset(pairs,tokenizer,original.context_length)
    optimizer=torch.optim.AdamW(model.training_parameters("experimental"),lr=lr)
    losses=[]
    for _ in range(epochs):
        model.train()
        for i in range(len(data)):
            x,y,mask=(v.unsqueeze(0).to(device) for v in data[i])
            optimizer.zero_grad(set_to_none=True)
            loss=masked_cross_entropy(model(x,route="experimental"),y,mask)
            loss.backward()
            optimizer.step()
            losses.append(float(loss.detach().item()))
    if frozen_digest(original)!=original_digest:
        raise RuntimeError("base weights changed")
    if any(not torch.equal(v,model.export_adapter("trusted")[k]) for k,v in trusted.items()):
        raise RuntimeError("trusted adapter changed")
    if any(file_digest(Path(k))!=v for k,v in before.items()):
        raise RuntimeError("protected assets changed")
    dest.parent.mkdir(parents=True,exist_ok=True)
    torch.save({"format":"llm-cha-unapproved-wiki-adapter-v0.8.0.15",
      "route":"unapproved_wikipedia","rank":rank,
      "adapter":model.export_adapter("experimental"),
      "candidate_ids":[r["id"] for r in rows],
      "source_urls":[r["source"] for r in rows],
      "base_hash":original_digest,"losses":losses,
      "approved":False,"trusted_deployable":False,"auto_promote":False,
      "truth_state":"EXTERNAL_UNVERIFIED"},dest)
    return {"device":str(device),"candidate_count":len(rows),
      "steps":len(losses),"first_loss":losses[0],"last_loss":losses[-1],
      "base_unchanged":True,"trusted_adapter_unchanged":True}

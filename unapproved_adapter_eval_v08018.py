"""v0.8.0.18: teacher-forced diagnostics for an isolated Wikipedia adapter."""
import math
import torch
import torch.nn.functional as F
from pathlib import Path
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from dual_adapters_v073 import DualAdapterModel, frozen_digest
from unapproved_llm_intake_v074446 import _read,DEFAULT_STORE

def evaluate(store,base_path,tokenizer_path,adapter_path):
    ck=torch.load(adapter_path,map_location="cpu",weights_only=True)
    if ck.get("route")!="unapproved_wikipedia" or ck.get("approved") is not False or ck.get("trusted_deployable") is not False:
        raise ValueError("invalid experimental checkpoint")
    base,_=LanguageModel.load_checkpoint(str(base_path),device=torch.device("cpu"))
    if frozen_digest(base)!=ck.get("base_hash"):
        raise ValueError("base checkpoint mismatch")
    tokenizer=Tokenizer.load(str(tokenizer_path))
    if tokenizer.vocab_size!=base.vocab_size:raise ValueError("vocab mismatch")
    adapted=DualAdapterModel(base,rank=int(ck["rank"]))
    adapted.experimental.load_state_dict(ck["adapter"],strict=True)
    adapted.eval()
    base.eval()
    indexed={r.get("id"):r for r in _read(store)["candidates"]}
    results=[]
    for cid in ck.get("candidate_ids",[]):
        row=indexed.get(cid)
        if row is None:raise ValueError("candidate missing: "+str(cid))
        question=row["subject"]+"についてWikipediaの未検証情報は？"
        answer="Wikipediaの未検証情報: "+row["natural_language"]
        prefix=tokenizer.encode("人: "+question+"\nAI: ",add_bos=True)
        target=tokenizer.encode(answer,add_eos=True)
        sequence=prefix+target
        # Match ConversationDataset's truncation logic.
        max_sequence=base.context_length+1
        if len(sequence)>max_sequence:
            keep=max(1,max_sequence-len(target))
            prefix=prefix[-keep:]
        if len(prefix)+len(target)>max_sequence:
            room=max_sequence-len(prefix)
            target=target[:max(1,room)]
        if not target:continue
        sequence=prefix+target
        x=torch.tensor([sequence[:-1]],dtype=torch.long)
        y=torch.tensor(sequence[1:],dtype=torch.long)
        first=max(0,len(prefix)-1)
        positions=torch.arange(first,len(sequence)-1)
        with torch.inference_mode():
            base_logits=base(x)[0,positions]
            adapter_logits=adapted(x,route="experimental")[0,positions]
            gold=y[0,positions]
            base_nll=F.cross_entropy(base_logits,gold).item()
            adapted_nll=F.cross_entropy(adapter_logits,gold).item()
            base_prob=torch.softmax(base_logits,dim=-1).gather(1,gold.unsqueeze(1)).mean().item()
            adapt_prob=torch.softmax(adapter_logits,dim=-1).gather(1,gold.unsqueeze(1)).mean().item()
            delta=(adapter_logits-base_logits).abs().mean().item()
        results.append({"candidate_id":cid,"target_tokens":len(gold),
            "base_nll":base_nll,"adapter_nll":adapted_nll,
            "nll_improvement":base_nll-adapted_nll,
            "base_target_probability":base_prob,
            "adapter_target_probability":adapt_prob,
            "mean_absolute_logit_delta":delta})
    if not results:return {"status":"NO_EVALUABLE"}
    return {"status":"EVALUATED","candidate_count":len(results),
            "mean_nll_improvement":sum(x["nll_improvement"] for x in results)/len(results),
            "results":results,"evaluation_type":"TRAINING_PAIRS_ONLY",
            "holdout_evaluated":False,"truth_state":"EXTERNAL_UNVERIFIED",
            "approved":False,"weights_changed":False}

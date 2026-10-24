"""v0.8.0.19: diagnostic paraphrase and unknown-prompt probes.

Paraphrases are held out as QUESTIONS only; answers are reused from training.
Therefore this is not an independent knowledge holdout.
"""
import torch
import torch.nn.functional as F
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from dual_adapters_v073 import DualAdapterModel, frozen_digest
from unapproved_llm_intake_v074446 import _read

def probe(store,base_path,tokenizer_path,adapter_path):
    ck=torch.load(adapter_path,map_location="cpu",weights_only=True)
    if (ck.get("route")!="unapproved_wikipedia" or ck.get("approved") is not False
            or ck.get("trusted_deployable") is not False):
        raise ValueError("unsafe adapter checkpoint")
    base,_=LanguageModel.load_checkpoint(str(base_path),device=torch.device("cpu"))
    if frozen_digest(base)!=ck.get("base_hash"):raise ValueError("base mismatch")
    tokenizer=Tokenizer.load(str(tokenizer_path))
    if tokenizer.vocab_size!=base.vocab_size:raise ValueError("vocab mismatch")
    adapted=DualAdapterModel(base,rank=int(ck["rank"]))
    adapted.experimental.load_state_dict(ck["adapter"],strict=True)
    base.eval();adapted.eval()
    rows={r.get("id"):r for r in _read(store)["candidates"]}
    known=[]
    unknown=[]
    def logits(prompt):
        ids=tokenizer.encode("人: "+prompt+"\nAI: ",add_bos=True)
        x=torch.tensor([ids[-base.context_length:]],dtype=torch.long)
        with torch.inference_mode():
            return base(x)[0,-1],adapted(x,route="experimental")[0,-1]
    for cid in ck.get("candidate_ids",[]):
        if cid not in rows:raise ValueError("candidate absent: "+str(cid))
        row=rows[cid]
        subject=row["subject"]
        answer="Wikipediaの未検証情報: "+row["natural_language"]
        targets=tokenizer.encode(answer,add_eos=True)
        for question in (subject+"とは何ですか？",subject+"について説明してください"):
            prefix=tokenizer.encode("人: "+question+"\nAI: ",add_bos=True)
            # Align scoring with ConversationDataset's maximum sequence logic.
            maximum=base.context_length+1
            if len(prefix)+len(targets)>maximum:
                prefix=prefix[-max(1,maximum-len(targets)):]
            target=targets[:max(1,maximum-len(prefix))]
            if not target:continue
            seq=prefix+target
            x=torch.tensor([seq[:-1]],dtype=torch.long)
            gold=torch.tensor(target,dtype=torch.long)
            with torch.inference_mode():
                begin=len(prefix)-1
                a=base(x)[0,begin:begin+len(target),:]
                b=adapted(x,route="experimental")[0,begin:begin+len(target),:]
                delta=float((F.cross_entropy(a,gold)-F.cross_entropy(b,gold)).item())
            known.append({"candidate_id":cid,"question":question,"nll_improvement":delta})
    # Unknown probes quantify distribution shift, not correctness/rejection.
    for question in ("架空の粒子XYZとは何ですか？","存在しない概念ABCについて教えて"):
        a,b=logits(question)
        pa=torch.softmax(a,dim=-1)
        pb=torch.softmax(b,dim=-1)
        unknown.append({"question":question,
            "mean_absolute_logit_delta":float((a-b).abs().mean().item()),
            "top1_changed":bool(a.argmax().item()!=b.argmax().item()),
            "probability_l1":float((pa-pb).abs().sum().item())})
    return {"status":"PROBED","paraphrase_count":len(known),"unknown_count":len(unknown),
        "paraphrase_results":known,"unknown_results":unknown,
        "mean_paraphrase_nll_improvement":sum(r["nll_improvement"] for r in known)/len(known) if known else None,
        "interpretation":"Paraphrase questions only; reference answers reused from training.",
        "independent_holdout":False,"unknown_rejection_measured":False,
        "truth_state":"EXTERNAL_UNVERIFIED","weights_changed":False,"approved":False}

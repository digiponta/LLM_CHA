"""v0.2.33.24: frozen copy output-bias, EOS, and position-oracle study.

Oracle variants are DIAGNOSTIC upper bounds, not deployable copying models.
No checkpoint training, writing, or model parameter mutation.
"""
import argparse,json,random
from pathlib import Path
import torch
import torch.nn.functional as F
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from algorithmic_copy_generalization_v023320 import make_pools,make_examples,generation
from diagnose_copy_mechanism_v023323 import output_context,next_logits

def stats(logits,candidate_ids,target_id):
    probs=F.softmax(logits,dim=-1)
    order=(logits>logits[target_id]).sum().item()+1
    restricted=torch.tensor(sorted(set(candidate_ids)),device=logits.device)
    local=logits[restricted]
    local_winner=int(restricted[local.argmax()])
    return {"gold_probability":float(probs[target_id]),
            "global_target_rank":int(order),
            "global_prediction":int(logits.argmax()),
            "candidate_prediction":local_winner,
            "candidate_target_rank":int((local>logits[target_id]).sum())+1 if target_id in candidate_ids else None,
            "candidate_target_present":target_id in candidate_ids}

def run_mode(model,source,marker,bos,eos,mode,max_steps=None):
    """Greedy free generation with strictly defined interventions.

    normal: unrestricted EOS as usual.
    source_candidates: only IDs in source plus EOS.
    known_length: disallow EOS before correct length; force EOS at length.
    source_and_length: both constraints.
    position_oracle: force target ID at every position (identity-copy upper bound).
    """
    if mode not in {"normal","source_candidates","known_length","source_and_length","position_oracle"}:
        raise ValueError(mode)
    result=[]
    steps=len(source)+1 if max_steps is None else max_steps
    for j in range(steps):
        if mode=="position_oracle":
            token=source[j] if j<len(source) else eos
        elif mode in {"known_length","source_and_length"} and j==len(source):
            token=eos
        else:
            context=output_context(source,result,marker,bos)
            logits=next_logits(model,context).clone()
            if mode in {"source_candidates","source_and_length"}:
                allowed=set(source)|{eos}
                mask=torch.ones_like(logits,dtype=torch.bool)
                mask[list(allowed)]=False
                logits[mask]=float("-inf")
            if mode in {"known_length","source_and_length"} and j<len(source):
                logits[eos]=float("-inf")
            token=int(logits.argmax())
        result.append(token)
        if token==eos:break
    return {"exact":result==source+[eos],
            "generated_ids":result,
            "content_exact_at_gold_length":result[:len(source)]==source,
            "eos_position":result.index(eos) if eos in result else None}

def compare_modes(model,examples,marker,bos,eos):
    modes=("normal","source_candidates","known_length","source_and_length","position_oracle")
    reports={}
    for mode in modes:
        rows=[run_mode(model,source,marker,bos,eos,mode) for source in examples]
        reports[mode]={"exact":sum(r["exact"] for r in rows),
                       "content_at_gold_length":sum(r["content_exact_at_gold_length"] for r in rows),
                       "total":len(rows),"cases":rows}
    return reports

def probe_logits(model,examples,marker,bos,eos,known,unseen):
    rows=[]
    for source in examples:
        # One fixed teacher-forced position per sequence, plus EOS position.
        j=len(source)//2
        ctx=output_context(source,source[:j],marker,bos)
        logits=next_logits(model,ctx)
        target=source[j]
        eos_logits=next_logits(model,output_context(source,source,marker,bos))
        rows.append({"source":source,"position":j,"token":target,
            "copy_step":stats(logits,set(source)|{eos},target),
            "end_step":stats(eos_logits,set(source)|{eos},eos),
            "mean_known_logit":float(logits[known].mean()),
            "mean_unseen_logit":float(logits[unseen].mean()),
            "target_logit":float(logits[target]),
            "eos_logit_at_copy_step":float(logits[eos])})
    return rows

def embedding_audit(model,known,unseen):
    with torch.inference_mode():
        in_w=model.embedding.weight
        out_w=model.lm_head.weight
        def measures(ids):
            x=in_w[ids];y=out_w[ids]
            return {"mean_input_norm":float(x.norm(dim=1).mean()),
                    "mean_output_norm":float(y.norm(dim=1).mean()),
                    "mean_input_output_cosine":float(F.cosine_similarity(x,y,dim=1).mean())}
        return {"known":measures(known),"unseen":measures(unseen)}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--models",nargs="+",default=[
        "model/model-llm-cha-algorithmic-copy-v023320.pt",
        "model/token_copy_factorial_v023322/combined.pt"])
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--device",choices=("auto","cpu","cuda"),default="auto")
    p.add_argument("--seed",type=int,2424)
    p.add_argument("--count",type=int,20)
    p.add_argument("--out",default="results/copy_output_bias_eos_v023324.json")
    a=p.parse_args()
    if a.count<1:raise ValueError("count must be positive")
    output=Path(a.out)
    if output.exists():raise FileExistsError(output)
    tok=Tokenizer.load(a.tokenizer)
    known,oldheld=make_pools(tok.vocab_size)
    unseen=list(range(88,104)) # unseen in task training of 0.2.33.20/22
    rng=random.Random(a.seed)
    # Fixed test groups shared between models, not used in training/selection.
    short=[[rng.choice(known) for _ in range(rng.randint(2,8))] for _ in range(a.count)]
    long=[[rng.choice(known) for _ in range(rng.randint(12,18))] for _ in range(a.count)]
    novel=[[rng.choice(unseen) for _ in range(rng.randint(2,8))] for _ in range(a.count)]
    mixed=[[rng.choice(known+unseen) for _ in range(rng.randint(2,8))] for _ in range(a.count)]
    groups={"short":short,"long":long,"novel":novel,"mixed":mixed}
    device=torch.device("cuda" if a.device=="auto" and torch.cuda.is_available() else "cpu" if a.device=="auto" else a.device)
    reports={}
    for path in a.models:
        model,ckpt=LanguageModel.load_checkpoint(path,device);model.eval()
        if model.vocab_size!=tok.vocab_size:raise ValueError("Vocabulary mismatch")
        marker=ckpt.get("metadata",{}).get("marker_id",7)
        if marker in set(known+unseen+[tok.bos_id,tok.eos_id]):raise ValueError("Bad marker")
        mreport={"embedding":embedding_audit(model,known,unseen),"groups":{}}
        for name,examples in groups.items():
            comparison=compare_modes(model,examples,marker,tok.bos_id,tok.eos_id)
            logits=probe_logits(model,examples,marker,tok.bos_id,tok.eos_id,known,unseen)
            mreport["groups"][name]={"modes":comparison,"logit_probes":logits}
            print(Path(path).name,name,{k:f"{v['exact']}/{v['total']}" for k,v in comparison.items()})
        reports[path]=mreport
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps({"version":"v0.2.33.24","read_only":True,
        "models":reports,
        "disclaimers":["Candidate restriction, known-length EOS and position oracle inject extra task information and are not independent natural decoding results",
          "Position oracle trivially copies target IDs and is only a mechanical ceiling, not model achievement",
          "Novel IDs are held out from task training but may exist in base pretraining",
          "Logit and embedding statistics are descriptive, not causal evidence",
          "Single seed and small synthetic probe sets",
          "Free decoding uses greedy, no repetition penalty"]},
        ensure_ascii=False,indent=2),encoding="utf8")
    print("Saved",output)
if __name__=="__main__":main()

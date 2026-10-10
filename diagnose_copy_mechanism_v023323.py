"""v0.2.33.23 frozen copy-mechanism diagnostics: paired input interventions.

No training and no mutation of model modules. Attention weights are descriptive,
not causal attribution. All probabilities refer to teacher-forced next-token steps.
"""
import argparse,json,math,random
from pathlib import Path
import torch
import torch.nn.functional as F
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from algorithmic_copy_generalization_v023320 import make_pools,make_examples,generation

def output_context(source,output_prefix,marker,bos):
    return [bos,marker]+list(source)+[marker]+list(output_prefix)

def next_logits(model,context):
    dev=next(model.parameters()).device
    with torch.inference_mode():
        return model(torch.tensor([context],dtype=torch.long,device=dev))[0,-1,:]

def copy_probability(model,source,position,marker,bos,output_prefix=None):
    # Hold the previously generated tokens fixed, avoiding autoregressive
    # cascade as a confound in a one-token source intervention.
    prefix=source[:position] if output_prefix is None else output_prefix
    logits=next_logits(model,output_context(source,prefix,marker,bos))
    prob=F.softmax(logits,dim=-1)
    return {"target_probability":float(prob[source[position]]),
            "target_rank":int((logits>logits[source[position]]).sum())+1,
            "argmax":int(logits.argmax())}

def intervention(model,seq,position,replacement,marker,bos):
    if replacement==seq[position]:raise ValueError("Replacement must differ")
    modified=list(seq);modified[position]=replacement
    # At copy position j, gold output prefix is unchanged by the intervention
    # (source[0:j]); measure both old-ID and new-ID probabilities.
    ctx1=output_context(seq,seq[:position],marker,bos)
    ctx2=output_context(modified,seq[:position],marker,bos)
    a=F.softmax(next_logits(model,ctx1),dim=-1)
    b=F.softmax(next_logits(model,ctx2),dim=-1)
    old=seq[position]
    return {"position":position,"old_id":old,"new_id":replacement,
            "old_id_probability_before":float(a[old]),
            "old_id_probability_after":float(b[old]),
            "new_id_probability_before":float(a[replacement]),
            "new_id_probability_after":float(b[replacement]),
            "new_id_probability_gain":float(b[replacement]-a[replacement]),
            "new_id_logit_rank_after":int((b>b[replacement]).sum())+1,
            "predicted_before":int(a.argmax()),"predicted_after":int(b.argmax()),
            "prediction_matches_replacement":int(b.argmax())==replacement}

def attention_snapshot(model,context):
    # Reproduce each block's pre-attention states with the same norm/residual
    # operations as model.py. Measures attention to the *source position* at
    # the next-token query. No gradients / causal contribution implied.
    dev=next(model.parameters()).device
    tok=torch.tensor([context],device=dev)
    with torch.inference_mode():
        x=model.embedding(tok)
        if model.position_embedding is not None:
            x=x+model.position_embedding(torch.arange(len(context),device=dev)).unsqueeze(0)
        matrices=[]
        for block in model.blocks:
            norm=block.norm1(x);att=block.attention
            q=att._split_heads(att.q_proj(norm))
            k=att._split_heads(att.k_proj(norm))
            scores=q@k.transpose(-2,-1)/math.sqrt(att.head_dim)
            if att.causal:
                mask=torch.triu(torch.ones(len(context),len(context),dtype=torch.bool,device=dev),diagonal=1)
                scores=scores.masked_fill(mask,float("-inf"))
            weights=scores.softmax(-1)
            matrices.append(weights[0,:,-1,:].detach().cpu().tolist())
            x=x+att(norm)
            x=x+block.ffn(block.norm2(x))
    return matrices

def inspect_attention(model,seq,position,marker,bos):
    prefix=seq[:position]
    ctx=output_context(seq,prefix,marker,bos)
    # Source starts at absolute position 2. At prediction of j-th copy
    # token, source token position is 2+j.
    source_idx=2+position
    weights=attention_snapshot(model,ctx)
    out=[]
    for layer,head_rows in enumerate(weights):
        out.append({"layer":layer,"heads":[
            {"head":h,"source_mass":float(row[source_idx]),
             "source_rank":1+sum(w>row[source_idx] for w in row),
             "top_attention_position":int(max(range(len(row)),key=lambda i:row[i]))}
            for h,row in enumerate(head_rows)]})
    return out

def eos_probe(model,seq,marker,bos,eos):
    # At correct completion, compare EOS probability with a nonterminal
    # source-copy token at all earlier gold-prefix positions.
    before=[]
    for j in range(len(seq)):
        p=F.softmax(next_logits(model,output_context(seq,seq[:j],marker,bos)),dim=-1)
        before.append({"position":j,"eos_probability":float(p[eos]),
                       "copy_probability":float(p[seq[j]]),
                       "argmax_is_eos":int(p.argmax())==eos})
    after=F.softmax(next_logits(model,output_context(seq,seq,marker,bos)),dim=-1)
    return {"precompletion":before,"final_eos_probability":float(after[eos]),
            "final_eos_top1":int(after.argmax())==eos}

def study_model(model,examples,known,novel,marker,bos,eos,seed):
    rng=random.Random(seed)
    cases=[]
    for seq in examples:
        j=rng.randrange(len(seq))
        known_alternatives=[x for x in known if x!=seq[j]]
        # A novel replacement is outside the v0.2.33.20 task-trained pool.
        replacements={"known":rng.choice(known_alternatives),
                      "unseen":rng.choice(novel)}
        record={"source":seq,"probe_position":j,"original":copy_probability(model,seq,j,marker,bos),
                "interventions":{name:intervention(model,seq,j,val,marker,bos)
                                  for name,val in replacements.items()},
                "attention":inspect_attention(model,seq,j,marker,bos),
                "eos":eos_probe(model,seq,marker,bos,eos)}
        cases.append(record)
    summary={}
    for kind in ("known","unseen"):
        vals=[r["interventions"][kind] for r in cases]
        summary[kind]={"mean_new_id_probability_gain":sum(v["new_id_probability_gain"] for v in vals)/len(vals),
                       "top1_replacement_rate":sum(v["prediction_matches_replacement"] for v in vals)/len(vals),
                       "mean_new_id_rank":sum(v["new_id_logit_rank_after"] for v in vals)/len(vals)}
    summary["mean_final_eos_probability"]=sum(r["eos"]["final_eos_probability"] for r in cases)/len(cases)
    summary["final_eos_top1_rate"]=sum(r["eos"]["final_eos_top1"] for r in cases)/len(cases)
    return {"summary":summary,"cases":cases}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--models",nargs="+",default=["model/model-llm-cha-algorithmic-copy-v023320.pt",
                                                  "model/token_copy_factorial_v023322/combined.pt"])
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--device",choices=("auto","cpu","cuda"),default="auto")
    p.add_argument("--seed",type=int,default=2388)
    p.add_argument("--count",type=int,default=12)
    p.add_argument("--out",default="results/copy_mechanism_diagnostic_v023323.json")
    a=p.parse_args()
    if a.count<1:raise ValueError("count must be positive")
    path=Path(a.out)
    if path.exists():raise FileExistsError(path)
    dev=torch.device("cuda" if a.device=="auto" and torch.cuda.is_available() else "cpu" if a.device=="auto" else a.device)
    tok=Tokenizer.load(a.tokenizer)
    known,held=make_pools(tok.vocab_size)
    # Exclude ALL training IDs in v0.2.33.22 (8..87).
    novel=list(range(88,104))
    example_groups=make_examples(a.seed,known,held,n_train=max(a.count,20),n_val=10,n_test=10)
    rng=random.Random(a.seed)
    # Fresh probes: mix short and long, without taking historical test arrays.
    short=example_groups["train"][:a.count]
    long=[[rng.choice(known) for _ in range(rng.randint(12,18))] for _ in range(a.count)]
    data={}
    for filename in a.models:
        model,ckpt=LanguageModel.load_checkpoint(filename,dev);model.eval()
        if model.vocab_size!=tok.vocab_size:raise ValueError("Model/tokenizer vocabulary mismatch")
        # use identical marker convention as previous controlled experiment
        marker=ckpt.get("metadata",{}).get("marker_id",7)
        if marker in known+novel:raise ValueError("Invalid marker")
        groups={}
        for label,examples in (("short",short),("long",long)):
            groups[label]=study_model(model,examples,known,novel,marker,tok.bos_id,tok.eos_id,a.seed)
            print(f"{Path(filename).name} {label}: {groups[label]['summary']}")
        data[filename]=groups
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps({"version":"v0.2.33.23","read_only":True,
        "checkpoint_selection":False,"models":data,
        "limitations":["Attention weights are descriptive; they are not proof of copying or causal influence",
                       "Single-position input intervention uses fixed gold output prefix",
                       "The novel IDs were excluded from v0.2.33.20 and v0.2.33.22 task training, but not necessarily base pretraining",
                       "Source mutation may change likelihood of many tokens; inspect both before/after probabilities",
                       "EOS results use teacher-forced continuation rather than free generation",
                       "Only a small number of synthetic probes are used"]},
        ensure_ascii=False,indent=2),encoding="utf-8")
    print("Saved",path)
if __name__=="__main__":main()

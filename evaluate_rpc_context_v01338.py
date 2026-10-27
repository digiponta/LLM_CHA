"""v0.13.38 read-only RPC context dependency experiment.
Shuffled condition changes prior history but preserves the last partner turn.
This distinguishes the contribution of earlier context from the last turn.
"""
import argparse
import json
import random
from pathlib import Path
from sweep_rpc_decoding_v01337 import choose_probes, repetition, generic

MODES=("FULL_CONTEXT","LAST_TURN","SHUFFLED_CONTEXT")

def split_history(s):
    lines=[x.strip() for x in s.splitlines() if x.strip()]
    if not lines or not lines[-1].startswith("相手: "):
        raise ValueError("RPC history must end with partner turn")
    return lines[:-1],lines[-1]

def context_variants(rows):
    if len(rows)<2:raise ValueError("require two distinct dialogues")
    variants=[]
    for i,r in enumerate(rows):
        prev,last=split_history(r["user"])
        donor=None
        for offset in range(1,len(rows)):
            candidate=rows[(i+offset)%len(rows)]
            if str(candidate["dialogue_id"])!=str(r["dialogue_id"]):
                donor=candidate;break
        if donor is None:raise ValueError("no other dialogue")
        fake_prior,_=split_history(donor["user"])
        variants.append({
            "FULL_CONTEXT":r["user"],
            "LAST_TURN":last,
            "SHUFFLED_CONTEXT":"\n".join(fake_prior+[last]),
            "donor_dialogue_id":donor["dialogue_id"],
        })
    return variants

def char_similarity(a,b,n=3):
    def grams(s):
        s="".join(s.split())
        if not s:return set()
        return {s[i:i+n] for i in range(max(1,len(s)-n+1))}
    x,y=grams(a),grams(b)
    return len(x&y)/len(x|y) if x|y else 1.0

def summary(items):
    count=len(items)
    return {
        "cases":count,
        "mean_tokens":sum(x["tokens"] for x in items)/count,
        "mean_repetition":sum(x["repetition"] for x in items)/count,
        "generic_reply":sum(x["generic_reply"] for x in items),
        "empty":sum(not x["text"].strip() for x in items),
        "mean_reference_char3_jaccard":sum(x["reference_char3_jaccard"] for x in items)/count,
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--model",type=Path,default=Path("results/rpc_sweep_v01336/rpc_candidate_100000.pt"))
    p.add_argument("--data",type=Path,default=Path("results/rpc_sft_full_v01333/rpc_sft_val_v01333.jsonl"))
    p.add_argument("--tokenizer",type=Path,default=Path("../LLM_GPU/model/tokenizer-v0.7-bpe.json"))
    p.add_argument("--output",type=Path,default=Path("results/rpc_context_dependency_v01338.json"))
    p.add_argument("--limit",type=int,default=48)
    p.add_argument("--seeds",type=int,default=3)
    p.add_argument("--seed",type=int,default=1337)
    p.add_argument("--max-new-tokens",type=int,default=64)
    p.add_argument("--temperature",type=float,default=0.7)
    p.add_argument("--top-k",type=int,default=20)
    p.add_argument("--repetition-penalty",type=float,default=1.2)
    a=p.parse_args()
    if a.limit<2 or a.seeds<1 or a.max_new_tokens<1 or a.top_k<1 or a.temperature<0 or a.repetition_penalty<1:
        p.error("invalid evaluation parameters")
    for f in (a.model,a.data,a.tokenizer):
        if not f.exists():p.error(f"missing {f}")
    if a.output.exists():p.error("report exists")
    import torch
    from chat import generate_reply
    from model import LanguageModel
    from tokenizer_bpe import Tokenizer
    from online_train import USER_PREFIX,AI_PREFIX
    from train_rpc_dialogue_sft_v01334 import read_rows
    probes=choose_probes(read_rows(a.data),a.limit)
    if len(probes)<a.limit:p.error("not enough validation probes")
    variants=context_variants(probes)
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tok=Tokenizer.load(str(a.tokenizer))
    model,_=LanguageModel.load_checkpoint(str(a.model),device=device)
    model.eval()
    details=[];by_mode={mode:[] for mode in MODES}
    with torch.no_grad():
        for i,(r,v) in enumerate(zip(probes,variants)):
            for seed_index in range(a.seeds):
                seed=a.seed+i*1009+seed_index
                outputs={}
                for mode in MODES:
                    user=v[mode]
                    prompt=f"{USER_PREFIX}{user}\n{AI_PREFIX}"
                    result=generate_reply(model,tok,prompt,a.max_new_tokens,
                                          a.temperature,a.top_k,a.repetition_penalty,seed=seed)
                    d={"text":result.text,"tokens":result.token_count,
                       "repetition":repetition(result.text),"generic_reply":generic(result.text),
                       "reference_char3_jaccard":char_similarity(result.text,r["assistant"])}
                    outputs[mode]=d
                    by_mode[mode].append(d)
                details.append({"dialogue_id":r["dialogue_id"],"utterance_id":r["utterance_id"],
                                "seed":seed,"reference":r["assistant"],
                                "full_user":r["user"],"last_user":v["LAST_TURN"],
                                "shuffled_user":v["SHUFFLED_CONTEXT"],
                                "donor_dialogue_id":v["donor_dialogue_id"],
                                "outputs":outputs,
                                "full_vs_last_char3_jaccard":char_similarity(outputs["FULL_CONTEXT"]["text"],outputs["LAST_TURN"]["text"]),
                                "full_vs_shuffled_char3_jaccard":char_similarity(outputs["FULL_CONTEXT"]["text"],outputs["SHUFFLED_CONTEXT"]["text"])})
    report={
        "version":"v0.13.38","split":"VALIDATION","model":str(a.model),
        "conditions":list(MODES),"limit":a.limit,"seeds_per_case":a.seeds,
        "decoding":{"temperature":a.temperature,"top_k":a.top_k,"repetition_penalty":a.repetition_penalty},
        "summary":{mode:summary(rows) for mode,rows in by_mode.items()},
        "paired":{"mean_full_last_similarity":sum(r["full_vs_last_char3_jaccard"] for r in details)/len(details),
                  "mean_full_shuffled_similarity":sum(r["full_vs_shuffled_char3_jaccard"] for r in details)/len(details),
                  "identical_full_last":sum(r["outputs"]["FULL_CONTEXT"]["text"]==r["outputs"]["LAST_TURN"]["text"] for r in details),
                  "identical_full_shuffled":sum(r["outputs"]["FULL_CONTEXT"]["text"]==r["outputs"]["SHUFFLED_CONTEXT"]["text"] for r in details)},
        "details":details,"production_unchanged":True,
        "caveats":["Shuffled prior is not a grammatical dialogue; compare as a perturbation only.",
                   "Text difference proves input sensitivity, not semantic correctness.",
                   "Character 3-gram overlap with one reference is not a measure of conversation quality.",
                   "No independent test set is consumed."]}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"summary":report["summary"],"paired":report["paired"]},ensure_ascii=False,indent=2))
    print("report:",a.output)
if __name__=="__main__":main()

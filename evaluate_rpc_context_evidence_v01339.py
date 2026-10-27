"""v0.13.39 matched-reference context evidence evaluation (validation only).
Scores answer-token conditional NLL under FULL / LAST / SHUFFLED, with
identical answer target and same model. No generation or training.
"""
import argparse,json,math
from pathlib import Path
import torch
import torch.nn.functional as F
from online_train import USER_PREFIX,AI_PREFIX
from sweep_rpc_decoding_v01337 import choose_probes
from evaluate_rpc_context_v01338 import context_variants,MODES
from train_rpc_dialogue_sft_v01334 import read_rows

def encode_case(tokenizer,user,answer,context_length):
    """Match ConversationDataset prompt truncation; reject answer truncation."""
    prompt=tokenizer.encode(f"{USER_PREFIX}{user}\n{AI_PREFIX}",add_bos=True)
    target=tokenizer.encode(answer,add_eos=True)
    maxseq=context_length+1
    if len(target)>=maxseq:raise ValueError("answer exceeds context")
    original_prompt_length=len(prompt)
    if len(prompt)+len(target)>maxseq:
        prompt=prompt[-(maxseq-len(target)):]
    seq=prompt+target
    x=seq[:-1]
    y=seq[1:]
    mask=[1 if i+1>=len(prompt) else 0 for i in range(len(y))]
    if sum(mask)!=len(target):raise ValueError("answer alignment failed")
    return x,y,mask,original_prompt_length-len(prompt),len(target)

@torch.no_grad()
def score(model,device,encoded):
    x,y,mask,_,_=encoded
    logits=model(torch.tensor([x],dtype=torch.long,device=device))[0]
    target=torch.tensor(y,dtype=torch.long,device=device)
    active=torch.tensor(mask,dtype=torch.bool,device=device)
    loss=F.cross_entropy(logits,target,reduction="none")
    return float(loss[active].sum().item()),int(active.sum().item())

def aggregate(details,mode):
    sums=[r["scores"][mode]["loss_sum"] for r in details]
    tokens=[r["scores"][mode]["tokens"] for r in details]
    return {"pairs":len(sums),"tokens":sum(tokens),"token_weighted_nll":sum(sums)/sum(tokens),
            "prompt_truncated_pairs":sum(r["scores"][mode]["prompt_truncated_tokens"]>0 for r in details)}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--model",type=Path,default=Path("results/rpc_sweep_v01336/rpc_candidate_100000.pt"))
    p.add_argument("--data",type=Path,default=Path("results/rpc_sft_full_v01333/rpc_sft_val_v01333.jsonl"))
    p.add_argument("--tokenizer",type=Path,default=Path("../LLM_GPU/model/tokenizer-v0.7-bpe.json"))
    p.add_argument("--output",type=Path,default=Path("results/rpc_context_evidence_v01339.json"))
    p.add_argument("--limit",type=int,default=200)
    p.add_argument("--seed",type=int,default=1335)
    a=p.parse_args()
    if a.limit<2:p.error("limit must be >=2")
    for f in (a.model,a.data,a.tokenizer):
        if not f.exists():p.error(f"missing {f}")
    if a.output.exists():p.error("output exists")
    from model import LanguageModel
    from tokenizer_bpe import Tokenizer
    rows=choose_probes(read_rows(a.data),a.limit,seed=a.seed)
    if len(rows)<a.limit:p.error("insufficient validation pairs")
    variants=context_variants(rows)
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model,_=LanguageModel.load_checkpoint(str(a.model),device=device)
    tokenizer=Tokenizer.load(str(a.tokenizer))
    model.eval()
    details=[]
    for row,v in zip(rows,variants):
        result={"dialogue_id":row["dialogue_id"],"utterance_id":row["utterance_id"],
                "reference":row["assistant"],"donor_dialogue_id":v["donor_dialogue_id"],"scores":{}}
        for mode in MODES:
            encoded=encode_case(tokenizer,v[mode],row["assistant"],model.context_length)
            loss_sum,tokens=score(model,device,encoded)
            result["scores"][mode]={"loss_sum":loss_sum,"tokens":tokens,
                                    "nll":loss_sum/tokens,"prompt_truncated_tokens":encoded[3]}
        result["delta_history"]=result["scores"]["LAST_TURN"]["nll"]-result["scores"]["FULL_CONTEXT"]["nll"]
        result["delta_shuffle"]=result["scores"]["SHUFFLED_CONTEXT"]["nll"]-result["scores"]["FULL_CONTEXT"]["nll"]
        details.append(result)
    aggs={mode:aggregate(details,mode) for mode in MODES}
    full=aggs["FULL_CONTEXT"]["token_weighted_nll"]
    report={"version":"v0.13.39","split":"VALIDATION","method":"teacher_forced_reference_answer_nll",
            "model":str(a.model),"sample_seed":a.seed,"summary":aggs,
            "delta_history":aggs["LAST_TURN"]["token_weighted_nll"]-full,
            "delta_shuffle":aggs["SHUFFLED_CONTEXT"]["token_weighted_nll"]-full,
            "positive_delta_history_cases":sum(d["delta_history"]>0 for d in details),
            "positive_delta_shuffle_cases":sum(d["delta_shuffle"]>0 for d in details),
            "details":details,"production_unchanged":True,
            "notes":["Same reference response evaluated against all three prompts.",
                     "Pair-wise deltas are over the same answer tokens, including EOS.",
                     "Context truncation counts are reported per mode; investigate before causal conclusions.",
                     "Reference NLL is not a direct measure of free-generation relevance.",
                     "Reserved test dataset is untouched."]}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:report[k] for k in ("summary","delta_history","delta_shuffle","positive_delta_history_cases","positive_delta_shuffle_cases")},ensure_ascii=False,indent=2))
    print("report:",a.output)
if __name__=="__main__":main()

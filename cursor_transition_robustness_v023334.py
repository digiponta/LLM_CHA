"""v0.2.33.34 — Transition State multi-seed robustness and action diagnostics.

Frozen backbone, matched data per seed. Training task families stay fixed.
An unseen composed action script is evaluated with a separately trained
script-conditioned model ONLY when specified by the task description; it is
not claimed that v0.2.33.33 knows how to execute arbitrary unseen programs.
"""
import argparse,json,random,statistics,copy
from pathlib import Path
import torch
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from algorithmic_copy_generalization_v023320 import make_pools
from cursor_generalization_v023332 import TASKS,instruction_actions,make_data,action_position
from cursor_action_state_v023333 import StatefulCursor,fit,generate

ARMS=("baseline","last_action","transition_state")
ACTIONS=("ADVANCE","STAY","SKIP","STOP")

def trace_error(gold,pred):
    limit=min(len(gold),len(pred))
    for j in range(limit):
        if gold[j]!=pred[j]:return j
    return None if len(gold)==len(pred) else limit

def diagnose(model,head,cases,marker,bos,eos):
    confusion=[[0]*4 for _ in range(4)]
    exact=0;first={};eos_correct=0;stay_loops=0
    by_task={name:{"exact":0,"total":0} for name in TASKS}
    for task,src in cases:
        actions,positions=instruction_actions(task,len(src))
        expected=[src[j] for j in positions]+[eos]
        r=generate(model,head,src,task,marker,bos,eos)
        actual=r["actions"]
        hit=r["output"]==expected
        exact+=int(hit);by_task[task]["exact"]+=int(hit);by_task[task]["total"]+=1
        eos_correct+=int(eos in r["output"] and r["output"].index(eos)==len(positions))
        err=trace_error(actions,actual)
        k="none" if err is None else str(err)
        first[k]=first.get(k,0)+1
        stay_loops+=int(any(all(x==1 for x in actual[j:j+4])
                            for j in range(max(0,len(actual)-3))))
        # Free rollouts only share gold action labels until the first mismatch.
        # This avoids comparing divergent states as if they had the same target.
        prefix=min(len(actions),len(actual),err if err is not None else len(actions))
        for j in range(prefix):
            confusion[actions[j]][actual[j]]+=1
        if err is not None and err<len(actions) and err<len(actual):
            confusion[actions[err]][actual[err]]+=1
    return {"exact":exact,"total":len(cases),"by_task":by_task,
            "eos_correct":eos_correct,"stay_loop_cases":stay_loops,
            "first_error_hist":first,
            "first_divergence_action_confusion":confusion}

def oracle_actions(task,length):
    return instruction_actions(task,length)[0]

def action_composition_probes():
    """Script-level held-out compositions; NOT treated as learned-model scores."""
    return {
      "alternate_advance_stay_skip_stop":[0,1,2,0,1,2,3],
      "stay_twice_then_skip":[0,1,1,2,0,3],
      "skip_then_stay_then_advance":[0,2,1,0,3]}

def run_seed(seed,args,model,marker,bos,eos,known,held):
    data=make_data(seed,known,held,args.train_count,args.val_count,args.test_count)
    outcome={}
    for arm in ARMS:
        torch.manual_seed(seed)
        head=StatefulCursor(model.d_model,arm).to(next(model.parameters()).device)
        epochs,best_epoch,best=fit(model,head,data["train"],data["validation"],
                                  marker,bos,eos,args.epochs,args.lr,seed)
        evaluations={}
        for group in ("test","long","unseen","mixed_ids","novel_extra"):
            evaluations[group]=diagnose(model,head,data[group],marker,bos,eos)
            print(f"seed={seed} {arm} {group}: {evaluations[group]['exact']}/{evaluations[group]['total']}")
        outcome[arm]={"best_epoch":best_epoch,"best_validation":best,
                      "history":epochs,"evaluation":evaluations}
    return outcome

def summarize(results):
    summary={}
    for arm in ARMS:
        summary[arm]={}
        for group in ("test","long","unseen","mixed_ids","novel_extra"):
            ratios=[run[arm]["evaluation"][group]["exact"]/
                    run[arm]["evaluation"][group]["total"] for run in results.values()]
            summary[arm][group]={"mean":statistics.mean(ratios),
                                 "min":min(ratios),"max":max(ratios),
                                 "stdev":statistics.stdev(ratios) if len(ratios)>1 else None,
                                 "per_seed":ratios}
    return summary

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--base",default="model/model-llm-cha-algorithmic-copy-v023320.pt")
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--seeds",type=int,nargs="+",default=[42,43,44])
    p.add_argument("--train-count",type=int,default=120)
    p.add_argument("--val-count",type=int,default=30)
    p.add_argument("--test-count",type=int,default=30)
    p.add_argument("--epochs",type=int,default=3)
    p.add_argument("--lr",type=float,default=.001)
    p.add_argument("--device",choices=("auto","cpu","cuda"),default="auto")
    p.add_argument("--out",default="results/cursor_transition_robustness_v023334.json")
    a=p.parse_args()
    if not a.seeds or len(set(a.seeds))!=len(a.seeds):raise ValueError("Seeds must be distinct")
    if min(a.train_count,a.val_count,a.test_count,a.epochs)<1 or a.lr<=0:raise ValueError("Invalid args")
    path=Path(a.out)
    if path.exists():raise FileExistsError("Output exists")
    device=torch.device("cuda" if a.device=="auto" and torch.cuda.is_available() else "cpu" if a.device=="auto" else a.device)
    model,ckpt=LanguageModel.load_checkpoint(a.base,device);model.eval()
    for param in model.parameters():param.requires_grad_(False)
    tok=Tokenizer.load(a.tokenizer)
    if model.vocab_size!=tok.vocab_size:raise ValueError("Tokenizer mismatch")
    known,held=make_pools(model.vocab_size)
    marker=ckpt.get("metadata",{}).get("marker_id",7)
    results={}
    for seed in a.seeds:
        results[str(seed)]=run_seed(seed,a,model,marker,tok.bos_id,tok.eos_id,known,held)
    result={"version":"v0.2.33.34","seed_results":results,
            "aggregate":summarize(results),
            "heldout_action_scripts_reference_only":action_composition_probes(),
            "methodology":["Three independently trained seeds per arm by default",
              "First-divergence confusion: only gold-aligned prefix and first divergent action; no forced gold history at inference",
              "The heldout script patterns are REFERENCE ONLY and NOT scored against trained task-conditioned model",
              "A valid unseen-script test needs a script-input architecture or train-heldout task family",
              "Three arms have different parameter counts; single frozen backbone",
              "No changes to DSS, Semantic Memory, Bridge, stable runtime"] }
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf8")
    print("Saved",path)
if __name__=="__main__":main()

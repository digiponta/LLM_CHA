"""v0.2.30.5: disentangle recovery command sensitivity and answer likelihood.

No training, no autonomous mode recognition claim. Tests how changing ONLY
the instruction affects scores for the same output targets; compare raw NLL
of intended responses across checkpoints and target ranking vs generic.
"""
import argparse, json
from pathlib import Path
from collections import defaultdict
import torch
import torch.nn.functional as F
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from prepare_prefix_recovery_v02304 import build
from evaluate_prefix_recovery_v02304 import generate, score

@torch.no_grad()
def recovery_recovery_answer_nll(model,tok,user,answer):
    # user already contains the full multi-turn prompt, as in
    # ConversationDataset(preformatted_prompts=True).
    prefix=tok.encode(user+"\nAI: ",add_bos=True)
    response=tok.encode(answer,add_eos=True)
    seq=prefix+response
    if len(seq)>model.context_length+1:
        raise ValueError("prompt + answer longer than model context")
    device=next(model.parameters()).device
    x=torch.tensor([seq[:-1]],dtype=torch.long,device=device)
    y=torch.tensor(seq[1:],dtype=torch.long,device=device)
    logits=model(x)[0].float()
    losses=F.cross_entropy(logits,y,reduction="none")
    return float(losses[len(prefix)-1:].mean().item()),len(response)

COMMANDS={"continue":"[CONTINUE] 同じ話題を続けて",
          "restart":"[RESTART] 最初から話題に沿って答え直して"}
GENERIC=("そうですね。","そうなんですか?")
def counterfactual_prompt(original,to_mode):
    old=COMMANDS["continue" if to_mode=="restart" else "restart"]
    new=COMMANDS[to_mode]
    if original.count(old)!=1:
        raise ValueError("one original recovery instruction required")
    return original.replace(old,new)

def candidate_summary(candidate_nll):
    correct=candidate_nll["target"]
    best_generic=min(candidate_nll[x] for x in ("generic_1","generic_2"))
    return {"target_nll":correct,
            "best_generic_nll":best_generic,
            "target_vs_generic_margin":best_generic-correct,
            "target_beats_generic":correct<best_generic}

def command_preference(nll_matched,nll_swapped):
    # Positive means current target answer more likely with its own command.
    return nll_swapped-nll_matched

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--model",action="append",help="NAME=CHECKPOINT")
    ap.add_argument("--tokenizer",default="../LLM_TRY/model/tokenizer-v0.7-bpe.json")
    ap.add_argument("--out",default="results/recovery_diagnosis_v02305.jsonl")
    ap.add_argument("--max-new-tokens",type=int,default=96)
    a=ap.parse_args()
    if a.max_new_tokens<1:ap.error("positive max new tokens needed")
    models={"continuation":"model/model-llm-cha-topic-continuation-v02302.pt",
            "recovery":"model/model-llm-cha-prefix-recovery-v02304.pt"}
    if a.model:
        models={}
        for spec in a.model:
            label,sep,path=spec.partition("=")
            if not sep or not label or not path:ap.error("use --model NAME=CHECKPOINT")
            models[label]=path
    cases=build()
    tok=Tokenizer.load(a.tokenizer)
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    out=Path(a.out)
    out.parent.mkdir(parents=True,exist_ok=True)
    totals=defaultdict(lambda:{"n":0,"target_better":0,"command_preferred":0,
                               "free_topic":0,"nll_sum":0., "delta_sum":0.})
    with out.open("w",encoding="utf-8") as f:
        for name,checkpoint in models.items():
            model,_=LanguageModel.load_checkpoint(checkpoint,device=device)
            model.eval()
            if model.vocab_size!=tok.vocab_size:raise ValueError("tokenizer vocabulary mismatch")
            for case in cases:
                prompt=case["user"]
                mode=case["mode"]
                opposite="restart" if mode=="continue" else "continue"
                swapped=counterfactual_prompt(prompt,opposite)
                target=case["assistant"]
                matched_nll,_=recovery_answer_nll(model,tok,prompt,target)
                swapped_nll,_=recovery_answer_nll(model,tok,swapped,target)
                candidates={"target":matched_nll}
                for i,text in enumerate(GENERIC,1):
                    candidates[f"generic_{i}"]=recovery_answer_nll(model,tok,prompt,text)[0]
                c=candidate_summary(candidates)
                delta=command_preference(matched_nll,swapped_nll)
                generated=generate(model,tok,prompt,a.max_new_tokens)
                free=score(case["topic"],mode,generated)
                record={"model":name,"topic":case["topic"],"mode":mode,
                        "target":target,"generated":generated,
                        "matched_target_nll":matched_nll,
                        "swapped_target_nll":swapped_nll,
                        "command_target_delta":delta,
                        "command_favors_intended_target":delta>0,
                        "candidate_nll":candidates,
                        **c,"free_lexical_topic":free["lexical_topic"],
                        "free_exact_topic":free["topic_exact"]}
                f.write(json.dumps(record,ensure_ascii=False)+"\n")
                k=(name,mode); s=totals[k]
                s["n"]+=1
                s["target_better"]+=int(c["target_beats_generic"])
                s["command_preferred"]+=int(delta>0)
                s["free_topic"]+=int(free["lexical_topic"])
                s["nll_sum"]+=matched_nll
                s["delta_sum"]+=delta
                print(f'{name:12} {mode:8} {case["topic"]:9} '
                      f'NLL={matched_nll:.4f} Δcommand={delta:+.4f} '
                      f'margin={c["target_vs_generic_margin"]:+.4f} '
                      f'free-topic={free["lexical_topic"]}')
    for (name,mode),s in totals.items():
        n=s["n"]
        print(f'{name}/{mode}: intended-command={s["command_preferred"]}/{n} '
              f'target>generic={s["target_better"]}/{n} '
              f'free-topic={s["free_topic"]}/{n} '
              f'mean-target-NLL={s["nll_sum"]/n:.4f} '
              f'mean-Δcommand={s["delta_sum"]/n:+.4f}')
    print("Saved:",out)
if __name__=="__main__":main()

"""v0.2.29.2: contrastive topic-to-answer ranking, no retraining.

Compare teacher-forced length-normalized answer NLL for candidate answers,
holding the input prompt constant. Report margins and wrong-topic confusions.
"""
import argparse,json
from collections import defaultdict
from pathlib import Path
import torch
import torch.nn.functional as F
from model import LanguageModel
from tokenizer_bpe import Tokenizer

DEFAULT_MODELS={
    "baseline":"model/model-llm-cha-v0227-baseline.pt",
    "persistence":"model/model-llm-cha-context-persistence-v0228.pt",
    "grounded":"model/model-llm-cha-topic-grounded-v02291.pt",
}

def assemble_candidates(rows,split):
    # All candidate answers are restricted to the same split.
    by_topic=defaultdict(list)
    for row in rows:
        if row["split"]==split:
            by_topic[row["topic"]].append(row["reference"])
    return dict(by_topic)

@torch.no_grad()
def answer_nll(model,tok,prompt,answer):
    prefix=tok.encode("人: "+prompt+"\nAI: ",add_bos=True)
    response=tok.encode(answer,add_eos=True)
    sequence=prefix+response
    if len(sequence)>model.context_length+1:
        raise ValueError("prompt + answer longer than model context")
    device=next(model.parameters()).device
    x=torch.tensor([sequence[:-1]],dtype=torch.long,device=device)
    y=torch.tensor(sequence[1:],dtype=torch.long,device=device)
    logits=model(x)[0].float()
    losses=F.cross_entropy(logits,y,reduction="none")
    assistant_losses=losses[len(prefix)-1:]
    return float(assistant_losses.mean().item()),len(response)

def rank_candidates(scores,gold_topic):
    # score: list of (topic, nll) pairs; lower = better
    if not scores or gold_topic not in {t for t,_ in scores}:
        raise ValueError("missing candidate or gold topic")
    ordered=sorted(scores,key=lambda item:item[1])
    gold=min(v for t,v in scores if t==gold_topic)
    wrong=min(v for t,v in scores if t!=gold_topic)
    return {"correct_nll":gold,"best_wrong_nll":wrong,
            "margin_wrong_minus_correct":wrong-gold,
            "top_topic":ordered[0][0],
            "correct_at_1":ordered[0][0]==gold_topic,
            "correct_rank":1+sum(v<gold for t,v in scores if t!=gold_topic)}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--fixture",default="data/topic_grounded_v02290/eval.jsonl")
    ap.add_argument("--tokenizer",default="../LLM_TRY/model/tokenizer-v0.7-bpe.json")
    ap.add_argument("--model",action="append",help="NAME=CHECKPOINT; repeatable")
    ap.add_argument("--out",default="results/topic_contrastive_v02292.jsonl")
    args=ap.parse_args()
    path=Path(args.fixture)
    if not path.is_file():ap.error("run prepare_topic_grounded_v02290.py first")
    rows=[json.loads(x) for x in path.read_text(encoding="utf-8-sig").splitlines() if x.strip()]
    models=dict(DEFAULT_MODELS)
    if args.model:
        models={}
        for spec in args.model:
            name,sep,checkpoint=spec.partition("=")
            if not sep or not name or not checkpoint:ap.error("--model NAME=CHECKPOINT")
            models[name]=checkpoint
    tok=Tokenizer.load(args.tokenizer)
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    out=Path(args.out);out.parent.mkdir(parents=True,exist_ok=True)
    summary=defaultdict(lambda:{"count":0,"correct":0,"margin_sum":0.0})
    with out.open("w",encoding="utf-8") as stream:
        for model_name,checkpoint in models.items():
            model,_=LanguageModel.load_checkpoint(checkpoint,device=device)
            model.eval()
            if model.vocab_size!=tok.vocab_size:raise ValueError("vocabulary mismatch")
            for split in ("train","holdout"):
                topics=assemble_candidates(rows,split)
                if len(topics)<2:raise ValueError("need at least two topics per split")
                # One canonical answer per topic avoids bias from train topic having 2 references.
                candidates={topic:answers[0] for topic,answers in topics.items()}
                for case in (r for r in rows if r["split"]==split):
                    nlls=[]
                    for topic,answer in candidates.items():
                        nll,_=answer_nll(model,tok,case["prompt"],answer)
                        nlls.append((topic,nll))
                    result=rank_candidates(nlls,case["topic"])
                    row={"model":model_name,"split":split,"topic":case["topic"],
                         "prompt":case["prompt"],"candidate_nll":dict(nlls),**result}
                    stream.write(json.dumps(row,ensure_ascii=False)+"\n")
                    key=(model_name,split)
                    summary[key]["count"]+=1
                    summary[key]["correct"]+=int(result["correct_at_1"])
                    summary[key]["margin_sum"]+=result["margin_wrong_minus_correct"]
                    print(f'{model_name:12} {split:7} {case["topic"]:9} '
                          f'top={result["top_topic"]:9} rank={result["correct_rank"]} '
                          f'margin={result["margin_wrong_minus_correct"]:+.4f}')
    for (name,split),s in summary.items():
        print(f'{name}/{split}: top1={s["correct"]}/{s["count"]}, '
              f'mean margin={s["margin_sum"]/s["count"]:+.4f}')
    print("Saved:",out)
if __name__=="__main__":main()

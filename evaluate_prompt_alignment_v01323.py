"""v0.13.23 read-only prompt-alignment diagnostics on checkpoint-bound QA.

A: exact trained question; B: paraphrase; C: evidence-in-prompt.
D is source quotation (non-generative oracle baseline).
No weights, truth records or approvals are modified.
"""
import argparse
import json
from pathlib import Path

def probes(row):
    subject=str(row.get("subject","")).strip()
    source=str(row.get("source_text","")).strip()
    question=str(row["user"])
    return [
        ("A_TRAINED_PROMPT",question),
        ("B_PARAPHRASE",f"「{subject}」に関係する元の記録を教えてください。"),
        ("C_GROUNDED_PROMPT",f"次の原文だけを根拠に「{subject}」に関係する内容を答えてください。原文: {source}"),
    ]

def evaluate_rows(rows,model,tokenizer,limit=3,max_new_tokens=96):
    from chat import generate_reply
    from grounded_unapproved_generation_v01321 import validate_generation
    results=[]
    for row in rows[:limit]:
        evidence={"source_text":row["source_text"]}
        for label,question in probes(row):
            # Same prompt construction as the incremental training dataset.
            prompt=f"人: {question}\nAI: "
            generated=generate_reply(
                model=model,tokenizer=tokenizer,prompt=prompt,
                max_new_tokens=max_new_tokens,temperature=0.0,
                top_k=20,repetition_penalty=1.05,
            )
            ok,reason=validate_generation(generated.text,evidence)
            results.append({"knowledge_id":row["knowledge_id"],"subject":row.get("subject"),
                "probe":label,"prompt":prompt,"raw_generation":generated.text,
                "generated_tokens":generated.token_count,
                "verbatim_grounded":ok,"validation":reason,
                "expected_answer":row["assistant"],"approval_state":"UNAPPROVED"})
        results.append({"knowledge_id":row["knowledge_id"],"subject":row.get("subject"),
            "probe":"D_SOURCE_QUOTATION","raw_generation":None,
            "generated_tokens":0,"verbatim_grounded":True,
            "validation":"SOURCE_QUOTATION_BASELINE","expected_answer":row["source_text"],
            "approval_state":"UNAPPROVED"})
    return results

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--model",type=Path,default=Path("model/model-gpu-v1.6.2-unapproved-qa-v01318.pt"))
    p.add_argument("--tokenizer",type=Path,default=Path("../LLM_GPU/model/tokenizer-v0.7-bpe.json"))
    p.add_argument("--data",type=Path,default=Path("results/unapproved_stratified_pairs_v01318.jsonl"))
    p.add_argument("--output",type=Path,default=Path("results/prompt_alignment_v01323.json"))
    p.add_argument("--limit",type=int,default=16)
    p.add_argument("--max-new-tokens",type=int,default=96)
    args=p.parse_args()
    if args.limit<1:p.error("limit must be >= 1")
    for path in (args.model,args.tokenizer,args.data):
        if not path.exists():p.error(f"missing: {path}")
    from model import LanguageModel
    from tokenizer_bpe import Tokenizer
    import torch
    from online_train import checkpoint_trained_fingerprints, pair_fingerprint
    from unapproved_corpus_learning_v0139 import load_jsonl
    rows=load_jsonl(args.data)
    bound=checkpoint_trained_fingerprints(args.model)
    rows=[r for r in rows if pair_fingerprint(r["user"],r["assistant"]) in bound]
    if not rows:p.error("no checkpoint-bound QA pairs")
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model,_=LanguageModel.load_checkpoint(str(args.model),device=device)
    tokenizer=Tokenizer.load(str(args.tokenizer))
    details=evaluate_rows(rows,model,tokenizer,args.limit,args.max_new_tokens)
    summary={}
    for key in ("A_TRAINED_PROMPT","B_PARAPHRASE","C_GROUNDED_PROMPT","D_SOURCE_QUOTATION"):
        subset=[r for r in details if r["probe"]==key]
        summary[key]={"cases":len(subset),"verbatim_grounded":sum(r["verbatim_grounded"] for r in subset)}
    report={"version":"v0.13.23","device":str(device),"model":str(args.model),
            "evaluation":"TRAINING_PAIRS_NOT_INDEPENDENT",
            "summary":summary,"details":details,"production_unchanged":True}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k!="details"},ensure_ascii=False,indent=2))
    print("report:",args.output)

if __name__=="__main__":main()

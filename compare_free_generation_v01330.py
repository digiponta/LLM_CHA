"""v0.13.30: E4/E8 B_RAW free-generation comparison; evaluation only.

Training-set examples and paraphrases are reported separately.
Lexical grounding is not semantic correctness or an independent holdout.
"""
import argparse
import json
from pathlib import Path

def first_divergence(reference, generated):
    for i,(x,y) in enumerate(zip(reference,generated)):
        if x!=y:return i
    return None if len(reference)==len(generated) else min(len(reference),len(generated))

def paraphrase(question,subject):
    return f"「{subject}」に関する原文の記述を教えてください。"

def evaluate_one(model,tokenizer,row,label,max_tokens):
    from chat import generate_reply
    from online_train import USER_PREFIX,AI_PREFIX
    from grounded_unapproved_generation_v01321 import validate_generation
    question=row["user"] if label=="EXACT" else paraphrase(row["user"],row.get("subject",""))
    prompt=f"{USER_PREFIX}{question}\n{AI_PREFIX}"
    result=generate_reply(model=model,tokenizer=tokenizer,prompt=prompt,
                          max_new_tokens=max_tokens,temperature=0,top_k=20,
                          repetition_penalty=1.0)
    expected=tokenizer.encode(row["assistant"],add_eos=True)
    prompt_ids=tokenizer.encode(prompt,add_bos=True)
    from torch import no_grad,tensor
    generated_ids=[]
    # generate_reply does not expose raw ids; compare full-token re-encoding only
    # when round-trip identity is preserved.
    recoded=tokenizer.encode(result.text)
    diverge=first_divergence(expected,recoded)
    source=row.get("source_text") or row["assistant"]
    grounded,reason=validate_generation(result.text,{"source_text":source})
    return {"subject":row.get("subject"),"knowledge_id":row.get("knowledge_id"),
            "probe":label,"question":question,"expected_answer":row["assistant"],
            "raw_generation":result.text,"generated_tokens":result.token_count,
            "first_divergence_reencoded":diverge,
            "roundtrip_note":"re-encoded decoded text; token-level mismatch may include BPE boundary changes",
            "grounded_excerpt":grounded,"grounding_reason":reason,
            "exact_text_match":result.text.strip()==row["assistant"].strip()}

def summarize(rows):
    n=len(rows)
    return {"cases":n,"exact_text_matches":sum(x["exact_text_match"] for x in rows),
            "grounded_excerpts":sum(x["grounded_excerpt"] for x in rows),
            "mean_generated_tokens":sum(x["generated_tokens"] for x in rows)/n if n else None,
            "first_token_matches_reencoded":sum(x["first_divergence_reencoded"]!=0 for x in rows)}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--e4",type=Path,default=Path("results/b_raw_epoch_v01329_E4.pt"))
    p.add_argument("--e8",type=Path,default=Path("results/b_raw_epoch_v01329_E8.pt"))
    p.add_argument("--data",type=Path,default=Path("results/unapproved_b_raw_v01326.jsonl"))
    p.add_argument("--tokenizer",type=Path,default=Path("../LLM_GPU/model/tokenizer-v0.7-bpe.json"))
    p.add_argument("--output",type=Path,default=Path("results/free_generation_compare_v01330.json"))
    p.add_argument("--limit",type=int,default=16)
    p.add_argument("--max-new-tokens",type=int,default=96)
    a=p.parse_args()
    if a.limit<1 or a.max_new_tokens<1:p.error("positive limits required")
    for x in (a.e4,a.e8,a.data,a.tokenizer):
        if not x.exists():p.error(f"missing {x}")
    import torch
    from model import LanguageModel
    from tokenizer_bpe import Tokenizer
    from unapproved_corpus_learning_v0139 import load_jsonl
    tokenizer=Tokenizer.load(str(a.tokenizer))
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    rows=load_jsonl(a.data)[:a.limit]
    if not rows:p.error("no data")
    details={};summary={}
    for label,path in (("E4",a.e4),("E8",a.e8)):
        model,_=LanguageModel.load_checkpoint(str(path),device=device)
        model.eval()
        current=[evaluate_one(model,tokenizer,row,probe,a.max_new_tokens)
                 for row in rows for probe in ("EXACT","PARAPHRASE")]
        details[label]=current
        summary[label]={kind:summarize([r for r in current if r["probe"]==kind])
                        for kind in ("EXACT","PARAPHRASE")}
    report={"version":"v0.13.30","evaluation":"TRAINING_PAIRS_AND_NONINDEPENDENT_PARAPHRASES",
            "summary":summary,"details":details,"production_unchanged":True,
            "stability_note":"Refer to v0.13.29 replay NLL; this script does not re-evaluate stability"}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    print("report:",a.output)

if __name__=="__main__":main()

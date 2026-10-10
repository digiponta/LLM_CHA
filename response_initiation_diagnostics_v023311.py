"""v0.2.33.11: response initiation vs continuation diagnostic.

Uses token-ID prefixes aligned with the FULL prompt+answer encoding to avoid
BPE boundary artifacts. No training, DSS, Memory or Bridge changes.
"""
import argparse,json,datetime
from pathlib import Path
import torch
from dialogue_guided_generation_v02322 import CheckpointGenerator
from input_output_copy_learning_v02339 import TRAIN_TEXTS,TESTS,prompt as raw_prompt

def short_prompt(text):
    return f"文章: {text}\n出力: "

def prefix_plan(tokenizer,question,answer,prefix_tokens):
    # Encode prompt and target separately, exactly as in response-only SFT.
    qids=tokenizer.encode(question,add_bos=True)
    aids=tokenizer.encode(answer,add_eos=True)
    n=min(prefix_tokens,len(aids)-1)
    return qids+aids[:n],aids[n:],n

def analyze(generator,question,answer,prefix_tokens=0,max_new_tokens=100):
    tok=generator.tokenizer;model=generator.model
    ids,target,n=prefix_plan(tok,question,answer,prefix_tokens)
    if len(ids)>model.context_length:
        raise ValueError("Prompt + prefix exceeds model context")
    x=torch.tensor([ids],dtype=torch.long,device=generator.device)
    with torch.inference_mode():
        scores=model(x)[0,-1]
        logits=torch.log_softmax(scores,dim=-1)
        truth=target[0]
        rank=1+int((scores>scores[truth]).sum().item())
        prob=float(logits[truth].exp())
        top1=int(scores.argmax())
        generated=model.generate(ids,max_new_tokens=max_new_tokens,
               temperature=0,top_k=20,eos_id=tok.eos_id,repetition_penalty=1.0)
    suffix=generated[len(ids):]
    # Match token IDs, not only decoded surface, for true prefix continuation.
    correct_run=0
    for expected,actual in zip(target,suffix):
        if expected!=actual:break
        correct_run+=1
    text=tok.decode(suffix).split("\n人:",1)[0].split("\nAI:",1)[0].strip()
    return {"prefix_tokens":n,"target_remaining_tokens":len(target),
            "first_correct_id":truth,"first_top1_id":top1,"first_rank":rank,
            "first_prob":prob,"first_top1":top1==truth,
            "exact_next_token_run":correct_run,"full_token_copy":suffix==target,
            "generated_text":text,"expected_suffix":tok.decode(target),
            "stopped_on_eos":bool(suffix and suffix[-1]==tok.eos_id)}

def evaluate(generators,cases,max_new_tokens=100):
    report=[]
    for category,answer in cases:
        formats={"raw":raw_prompt(answer),"short":short_prompt(answer)}
        outputs={}
        for name,g in generators.items():
            formats_out={}
            for form,q in formats.items():
                # Full answer encoded once, prefix lengths from this answer's token IDs.
                formats_out[form]={str(n):analyze(g,q,answer,n,max_new_tokens)
                                   for n in (0,1,3)}
            outputs[name]=formats_out
        report.append({"category":category,"answer":answer,"outputs":outputs})
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--base",default="model/model-llm-cha-response-quality-v0221.pt")
    p.add_argument("--copy",default="model/model-llm-cha-copy-v02339.pt")
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--device",choices=("auto","cpu","cuda"),default="auto")
    p.add_argument("--max-new-tokens",type=int,default=100)
    p.add_argument("--out",default="results/response_initiation_v023311.json")
    a=p.parse_args()
    if a.max_new_tokens<1:raise ValueError("Invalid token budget")
    path=Path(a.out)
    if path.exists():raise FileExistsError(path)
    models={"base":CheckpointGenerator(a.base,a.tokenizer,a.device),
            "copy":CheckpointGenerator(a.copy,a.tokenizer,a.device)}
    cases=[("seen",s) for s in TRAIN_TEXTS[:3]]+TESTS[:3]+TESTS[3:5]
    records=evaluate(models,cases,a.max_new_tokens)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps({"version":"v0.2.33.11",
         "generated_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),
         "training_performed":False,"promotion_eligible":False,
         "notes":["Gold answer prefixes are supplied, so successful suffixes do not demonstrate unassisted copying",
                  "Prompt-form effects may reflect distribution mismatch, not only answer initiation",
                  "Token-ID exact comparison includes EOS and can differ from human-readable equivalence"],
         "cases":records},ensure_ascii=False,indent=2),encoding="utf-8")
    for row in records:
        print(f"[{row['category']}] {row['answer']}")
        for model,forms in row["outputs"].items():
            for form,values in forms.items():
                for n,rec in values.items():
                    print(f" {model:5s} {form:5s} prefix={n} rank={rec['first_rank']:4d} "
                          f"run={rec['exact_next_token_run']:2d} full={rec['full_token_copy']} "
                          f"output={rec['generated_text']!r}")
    print("Saved:",path)
if __name__=="__main__":main()

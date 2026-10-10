"""v0.2.33.10: frozen checkpoint token-level copy diagnostics.

Reports tokenizer roundtrip, response target alignment, teacher-forced token
accuracy, and divergence between raw greedy and repetition-penalized decoding.
"""
import argparse,json,datetime
from pathlib import Path
import torch
from dialogue_guided_generation_v02322 import CheckpointGenerator
from input_output_copy_learning_v02339 import TRAIN_TEXTS,TESTS,prompt
from train_purpose_sft_v02324 import encode_row

def inspect_alignment(tok,text,context_length):
    p=prompt(text)
    enc=encode_row(tok,{"id":"diagnostic","prompt":p,"answer":text},context_length)
    x,y=enc
    active=(y!=-100).nonzero(as_tuple=False).flatten().tolist()
    answer_ids=tok.encode(text,add_eos=True)
    target_ids=[int(y[i]) for i in active]
    return {"target_alignment_ok":target_ids==answer_ids,
            "prompt_roundtrip":tok.decode(tok.encode(p))==p,
            "answer_roundtrip":tok.decode(tok.encode(text))==text,
            "answer_token_count":len(answer_ids),
            "prompt_token_count":len(tok.encode(p,add_bos=True)),
            "active_target_count":len(active)}

def token_predictions(generator,text,limit=15):
    tok=generator.tokenizer;model=generator.model
    x,y=encode_row(tok,{"id":"diagnostic","prompt":prompt(text),"answer":text},model.context_length)
    ids=(y!=-100).nonzero(as_tuple=False).flatten()
    with torch.inference_mode():
        logits=model(x.unsqueeze(0).to(generator.device))[0,ids.to(generator.device)]
        correct=y[ids].to(generator.device)
        logprob=torch.log_softmax(logits,dim=-1)
        probabilities=logprob.gather(-1,correct.unsqueeze(-1)).exp().squeeze(-1)
        sorted_greater=(logits>logits.gather(-1,correct.unsqueeze(-1))).sum(dim=-1)+1
        top1=logits.argmax(dim=-1)
    details=[]
    for i in range(min(limit,len(correct))):
        target=int(correct[i]);predicted=int(top1[i])
        details.append({"position":i,"target_id":target,"target_piece":tok.decode([target]),
                        "greedy_id":predicted,"greedy_piece":tok.decode([predicted]),
                        "rank":int(sorted_greater[i]),"prob":round(float(probabilities[i]),6),
                        "top1_correct":target==predicted})
    return {"teacher_nll":float(-logprob.gather(-1,correct.unsqueeze(-1)).mean()),
            "teacher_top1_accuracy":float((top1==correct).float().mean()),
            "first_token_rank":int(sorted_greater[0]),
            "first_token_probability":float(probabilities[0]),
            "token_details":details}

def decode_variants(generator,text,max_new_tokens=90):
    tok=generator.tokenizer;model=generator.model;ids=tok.encode(prompt(text),add_bos=True)
    result={}
    for penalty in (1.0,1.05):
        with torch.inference_mode():
            output=model.generate(ids,max_new_tokens=max_new_tokens,eos_id=tok.eos_id,
                                  temperature=0,top_k=20,repetition_penalty=penalty)
        decoded=tok.decode(output[len(ids):]).split("\n人:",1)[0].split("\nAI:",1)[0].strip()
        result["penalty_1" if penalty==1.0 else "penalty_1_05"]={
            "text":decoded,"exact_copy":decoded==text,
            "first_generated_id":int(output[len(ids)]) if len(output)>len(ids) else None,
            "generated_eos":bool(output[-1]==tok.eos_id)}
    return result

def diagnose(generators,samples,max_new_tokens=90):
    report=[]
    for kind,text in samples:
        models={}
        for name,g in generators.items():
            models[name]={"alignment":inspect_alignment(g.tokenizer,text,g.model.context_length),
                          "teacher_forcing":token_predictions(g,text),
                          "generation":decode_variants(g,text,max_new_tokens)}
        report.append({"kind":kind,"input":text,"models":models})
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--base",default="model/model-llm-cha-response-quality-v0221.pt")
    p.add_argument("--copy",default="model/model-llm-cha-copy-v02339.pt")
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--device",choices=("auto","cpu","cuda"),default="auto")
    p.add_argument("--max-new-tokens",type=int,default=90)
    p.add_argument("--out",default="results/token_copy_diagnostics_v023310.json")
    a=p.parse_args()
    if a.max_new_tokens<1:raise ValueError("max-new-tokens must be positive")
    out=Path(a.out)
    if out.exists():raise FileExistsError(f"Refusing overwrite: {out}")
    models={"base":CheckpointGenerator(a.base,a.tokenizer,a.device),
            "copy":CheckpointGenerator(a.copy,a.tokenizer,a.device)}
    cases=[("seen",s) for s in TRAIN_TEXTS[:3]]+TESTS[:3]+TESTS[3:5]+TESTS[-1:]
    result=diagnose(models,cases,a.max_new_tokens)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps({"experiment":"v0.2.33.10",
        "generated_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "training_performed":False,"promotion_eligible":False,
        "caveats":["Small diagnostic sample, not independent benchmark",
                   "Teacher-forced predictions do not equal free-generation performance",
                   "Decoded roundtrip may vary with tokenizer normalization",
                   "Greedy decoding truncates dialogue-turn delimiters for comparison"],
        "results":result},ensure_ascii=False,indent=2),encoding="utf-8")
    for row in result:
        print(f"[{row['kind']}] {row['input']}")
        for name,m in row["models"].items():
            a0=m["alignment"];tf=m["teacher_forcing"];g=m["generation"]
            print(f" {name}: roundtrip={a0['answer_roundtrip']} align={a0['target_alignment_ok']} "
                  f"top1={tf['teacher_top1_accuracy']:.3f} first_rank={tf['first_token_rank']} "
                  f"NLL={tf['teacher_nll']:.3f}")
            print("  greedy: ",repr(g["penalty_1"]["text"]))
            print("  penalty:",repr(g["penalty_1_05"]["text"]))
    print("Saved",out)
if __name__=="__main__":main()

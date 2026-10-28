"""v0.13.58.12 Offline matched raw generation: BASE / A / B / C.

Reuses v0.13.56 probes and sampling settings. Does not call retrieval,
memory, Wikipedia or external APIs. All generations are experimental;
no automatic winner or production promotion.
"""
import argparse,hashlib,json
from pathlib import Path
from compare_literature_generation_v01356 import PROMPTS,repetition

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def compare(paths,tokenizer,output,max_new_tokens=80,temperature=.6,top_k=20,
            repetition_penalty=1.1,seed=135812,prompts=None):
    import torch
    from model import LanguageModel
    from tokenizer_bpe import Tokenizer
    if output.exists():raise FileExistsError("output exists: "+str(output))
    inputs=[*paths.values(),tokenizer]
    if len({p.resolve() for p in inputs+[output]})!=len(inputs)+1:raise ValueError("overlap input/output")
    tok=Tokenizer.load(str(tokenizer))
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    models={}
    for name,path in paths.items():
        model,_=LanguageModel.load_checkpoint(str(path),device=device)
        if model.vocab_size!=tok.vocab_size:raise ValueError(name+": vocab mismatch")
        models[name]=model.eval()
    cases=[]
    for index,item in enumerate(prompts if prompts is not None else PROMPTS):
        prefix=tok.encode(item["prompt"],add_bos=True)
        if not prefix:raise ValueError("empty prefix")
        row={"id":item["id"],"category":item["category"],"prompt":item["prompt"],
             "prompt_tokens":len(prefix),"outputs":{}}
        for name,model in models.items():
            torch.manual_seed(seed+index)
            if torch.cuda.is_available():torch.cuda.manual_seed_all(seed+index)
            with torch.no_grad():
                tokens=model.generate(prefix,max_new_tokens=max_new_tokens,eos_id=tok.eos_id,
                   temperature=temperature,top_k=top_k,repetition_penalty=repetition_penalty)
            new=tokens[len(prefix):]
            text=tok.decode(new,skip_special_tokens=True)
            row["outputs"][name]={"text":text,"generated_tokens":len(new),
                "empty":not text.strip(),**repetition(text)}
        cases.append(row)
    report={"version":"v0.13.58.12","status":"RAW_FOUR_MODEL_COMPARISON",
       "device":str(device),"models":list(models),
       "settings":{"max_new_tokens":max_new_tokens,"temperature":temperature,
        "top_k":top_k,"repetition_penalty":repetition_penalty,"seed":seed},
       "input_sha256":{**{name:sha(path) for name,path in paths.items()},"tokenizer":sha(tokenizer)},
       "cases":cases,"human_review_complete":False,"independent_holdout_verified":False,
       "production_promotion_allowed":False,"automatic_winner":None,
       "notes":["Raw LM completion is not full LLM_CHA runtime.",
        "The seven reused probes are exploratory, not independent holdout.",
        "Matched seeds do not imply matched output tokens.",
        "Keyword-based guard is a smoke check, not a semantic correctness test."]}
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open("x",encoding="utf-8") as f:json.dump(report,f,ensure_ascii=False,indent=2)
    return report

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--base",type=Path,default=Path("model/model-llm-try-nagato-chat-v94.pt"))
    for k in "ABC":ap.add_argument("--"+k.lower(),type=Path,default=Path(f"results/offline_replay_v0135811/candidate_{k}.pt"))
    ap.add_argument("--tokenizer",type=Path,default=Path("../LLM_GPU/model/tokenizer-v0.7-bpe.json"))
    ap.add_argument("--output",type=Path,default=Path("results/offline_four_model_generation_v0135812.json"))
    ap.add_argument("--max-new-tokens",type=int,default=80)
    ap.add_argument("--temperature",type=float,default=.6)
    ap.add_argument("--top-k",type=int,default=20)
    ap.add_argument("--repetition-penalty",type=float,default=1.10)
    ap.add_argument("--seed",type=int,default=135812)
    a=ap.parse_args()
    if a.max_new_tokens<1 or a.top_k<1 or a.temperature<0 or a.repetition_penalty<=0:
        ap.error("invalid generation parameters")
    paths={"base":a.base,"A":a.a,"B":a.b,"C":a.c}
    for label,path in [*paths.items(),("tokenizer",a.tokenizer)]:
        if not path.is_file():ap.error(f"missing {label}: {path}")
    result=compare(paths,a.tokenizer,a.output,a.max_new_tokens,a.temperature,
                   a.top_k,a.repetition_penalty,a.seed)
    print(json.dumps({"status":result["status"],"cases":len(result["cases"]),
                      "models":result["models"],"automatic_winner":None},ensure_ascii=False))
    print("report:",a.output)
if __name__=="__main__":main()

"""v0.13.56 isolated raw-generation comparison, no chat retrieval/gates.

Identical tokenizer, prompts, generation configuration, and per-prompt RNG
seeds for BASE and LITERATURE. Human fluency/persona evaluation remains required.
"""
import argparse,hashlib,json,re
from pathlib import Path

PROMPTS=[
 {"id":"casual","category":"conversation","prompt":"人: こんにちは。今日は何をしていたの？\nAI: "},
 {"id":"persona","category":"persona","prompt":"人: あなたは誰ですか。\nAI: "},
 {"id":"followup","category":"conversation","prompt":"人: 今日は読書をしました。\nAI: そうなんだ。\n人: どんな本が好き？\nAI: "},
 {"id":"foundation","category":"free_prose","prompt":"静かな朝、窓の外には"},
 {"id":"foundation2","category":"free_prose","prompt":"私が昨日考えていたことは"},
 {"id":"literature","category":"literature","prompt":"吾輩は猫である。"},
 {"id":"explanation","category":"knowledge","prompt":"人: 量子力学とは何ですか。\nAI: "}
]
def repetition(text):
    chars=[c for c in text if not c.isspace()]
    if len(chars)<4:return {"repeated_bigram_fraction":0.0,"unique_bigram_fraction":1.0}
    pairs=["".join(chars[i:i+2]) for i in range(len(chars)-1)]
    unique=len(set(pairs))/len(pairs)
    return {"repeated_bigram_fraction":round(1-unique,4),
            "unique_bigram_fraction":round(unique,4)}
def fingerprint(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def compare(base,literature,tokenizer,output,max_new_tokens=80,temperature=0.6,
            top_k=20,penalty=1.10,seed=1356,prompts=None):
    import torch
    from model import LanguageModel
    from tokenizer_bpe import Tokenizer
    if output.exists():raise FileExistsError("refusing overwrite")
    if output.resolve() in {p.resolve() for p in (base,literature,tokenizer)}:
        raise ValueError("output overlaps protected input")
    tok=Tokenizer.load(str(tokenizer))
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    models={}
    for name,path in [("base",base),("literature",literature)]:
        model,_=LanguageModel.load_checkpoint(str(path),device=device)
        if model.vocab_size!=tok.vocab_size:raise ValueError(f"{name}: tokenizer/model vocab mismatch")
        models[name]=model.eval()
    cases=[]
    for index,item in enumerate(prompts if prompts is not None else PROMPTS):
        prefix=tok.encode(item["prompt"],add_bos=True)
        if not prefix:raise ValueError("empty prompt tokenization")
        row={"id":item["id"],"category":item["category"],"prompt":item["prompt"],
             "prompt_token_count":len(prefix),"outputs":{}}
        for name,model in models.items():
            # Reset CPU and CUDA seed for each model and each prompt.
            torch.manual_seed(seed+index)
            if torch.cuda.is_available():torch.cuda.manual_seed_all(seed+index)
            tokens=model.generate(prefix,max_new_tokens=max_new_tokens,eos_id=tok.eos_id,
                 temperature=temperature,top_k=top_k,repetition_penalty=penalty)
            new=tokens[len(prefix):]
            generated=tok.decode(new,skip_special_tokens=True)
            row["outputs"][name]={"text":generated,"generated_tokens":len(new),
                                  **repetition(generated)}
        cases.append(row)
    result={"version":"v0.13.56","status":"RAW_GENERATION_COMPARISON",
        "device":str(device),
        "settings":{"max_new_tokens":max_new_tokens,"temperature":temperature,
                    "top_k":top_k,"repetition_penalty":penalty,"seed":seed},
        "fingerprints":{name:fingerprint(path) for name,path in
                         [("base",base),("literature",literature),("tokenizer",tokenizer)]},
        "cases":cases,
        "automatic_winner":None,
        "human_review_required":True,
        "notes":["This is raw LM continuation, not end-to-end LLM_CHA runtime.",
                 "Bigram uniqueness is descriptive and does not prove quality.",
                 "Same seed controls sampling but does not make token choices identical.",
                 "Novel may have appeared in prior model training; not independent holdout."]}
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open("x",encoding="utf-8") as f:json.dump(result,f,ensure_ascii=False,indent=2)
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--base",type=Path,default=Path("model/model-llm-try-nagato-chat-v94.pt"))
    p.add_argument("--literature",type=Path,default=Path("results/literature_candidate_v01355.pt"))
    p.add_argument("--tokenizer",type=Path,default=Path("../LLM_GPU/model/tokenizer-v0.7-bpe.json"))
    p.add_argument("--output",type=Path,default=Path("results/generation_comparison_v01356.json"))
    p.add_argument("--max-new-tokens",type=int,default=80)
    p.add_argument("--temperature",type=float,default=0.6)
    p.add_argument("--top-k",type=int,default=20)
    p.add_argument("--repetition-penalty",type=float,default=1.10)
    p.add_argument("--seed",type=int,default=1356)
    a=p.parse_args()
    if a.max_new_tokens<1 or a.top_k<1 or a.repetition_penalty<=0 or a.temperature<0:
        p.error("invalid generation parameters")
    for f in (a.base,a.literature,a.tokenizer):
        if not f.is_file():p.error(f"missing input: {f}")
    result=compare(a.base,a.literature,a.tokenizer,a.output,a.max_new_tokens,
                   a.temperature,a.top_k,a.repetition_penalty,a.seed)
    print(json.dumps({"status":result["status"],"cases":len(result["cases"]),
                      "human_review_required":True,"automatic_winner":None},ensure_ascii=False))
    print("report:",a.output)
if __name__=="__main__":main()

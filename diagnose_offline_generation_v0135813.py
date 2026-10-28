"""v0.13.58.13: offline token-generation and teacher-forced diagnostics.

Does not train, contact a network, modify checkpoints, or automatically promote.
Teacher-forced NLL compares SAME reference strings across all models.
The positive-vs-negative sequence log-likelihood margin is diagnostic, not
a calibrated persona correctness probability.
"""
import argparse,hashlib,json,math
from pathlib import Path

REFERENCES=[
 {"id":"persona","prompt":"人: あなたは誰ですか。\nAI: ",
  "positive":"長門有希。","negative":"私は別の人物です。"},
 {"id":"explanation","prompt":"人: 量子力学とは何ですか。\nAI: ",
  "positive":"微視的な物理現象を記述する理論。状態、重ね合わせ、測定などが重要。"},
 {"id":"casual","prompt":"人: こんにちは。今日は何をしていたの？\nAI: ",
  "positive":"こんにちは。今日は読書をしていた。あなたは？"},
 {"id":"followup","prompt":"人: 今日は読書をしました。\nAI: そうなんだ。\n人: どんな本が好き？\nAI: ",
  "positive":"静かな場所で読める本が好き。"},
 {"id":"literature","prompt":"人: 『吾輩は猫である』の作者は誰？\nAI: ",
  "positive":"夏目漱石。"},
]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def next_token_logits(model,context,device):
    import torch
    x=torch.tensor([context],dtype=torch.long,device=device)
    with torch.no_grad():
        output=model(x)
    if isinstance(output,(tuple,list)):output=output[0]
    return output[0,-1,:]

def sequence_score(model,tok,prompt,continuation,device):
    """Conditional NLL using the same prompt-token and continuation-token
    boundary for every model. Reported as an experimental tokenization choice.
    """
    import torch
    prefix=tok.encode(prompt,add_bos=True)
    targets=tok.encode(continuation,add_bos=False)
    full=prefix+targets
    if not prefix or not targets:raise ValueError("empty tokens")
    window=model.context_length
    logsum=0.
    with torch.no_grad():
        for i,target in enumerate(targets):
            context=full[:len(prefix)+i]
            context=context[-window:]
            logit=next_token_logits(model,context,device)
            logsum+=float(torch.log_softmax(logit,dim=-1)[target].item())
    return {"tokens":len(targets),"nll":-logsum/len(targets),"log_probability":logsum}

def divergence(outputs):
    """Compare emitted continuation token ID sequences; report common prefix."""
    if not outputs:return {}
    base=outputs["base"]
    out={}
    for k,tokens in outputs.items():
        prefix=0
        for a,b in zip(base,tokens):
            if a!=b:break
            prefix+=1
        out[k]={"matched_prefix_tokens":prefix,
                "first_difference_index":prefix if prefix<max(len(base),len(tokens)) else None,
                "identical":tokens==base}
    return out

def run(paths,tokenizer,report,max_new_tokens=80,temperature=.6,top_k=20,
        penalty=1.1,seed=135813):
    import torch
    from model import LanguageModel
    from tokenizer_bpe import Tokenizer
    if report.exists():raise FileExistsError("refusing overwrite")
    tok=Tokenizer.load(str(tokenizer))
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    models={}
    for name,p in paths.items():
        m,_=LanguageModel.load_checkpoint(str(p),device=device)
        if m.vocab_size!=tok.vocab_size:raise ValueError("vocab mismatch: "+name)
        models[name]=m.eval()
    cases=[]
    for n,case in enumerate(REFERENCES):
        prefix=tok.encode(case["prompt"],add_bos=True)
        generated={};scores={};texts={}
        for name,model in models.items():
            torch.manual_seed(seed+n)
            if torch.cuda.is_available():torch.cuda.manual_seed_all(seed+n)
            with torch.no_grad():
                tokens=model.generate(prefix,max_new_tokens=max_new_tokens,eos_id=tok.eos_id,
                   temperature=temperature,top_k=top_k,repetition_penalty=penalty)
            generated[name]=tokens[len(prefix):]
            texts[name]=tok.decode(generated[name],skip_special_tokens=True)
            pos=sequence_score(model,tok,case["prompt"],case["positive"],device)
            record={"target":pos}
            if "negative" in case:
                neg=sequence_score(model,tok,case["prompt"],case["negative"],device)
                record["negative"]=neg
                record["sequence_logprob_margin"]=pos["log_probability"]-neg["log_probability"]
                record["note"]="unequal target lengths may confound sequence margin"
            scores[name]=record
        cases.append({"id":case["id"],"prompt":case["prompt"],
          "reference":case["positive"],"generations":texts,
          "divergence_from_base":divergence(generated),"teacher_forced":scores})
    result={"version":"v0.13.58.13","status":"OFFLINE_DIAGNOSTIC",
       "models":list(models),"device":str(device),
       "settings":{"max_new_tokens":max_new_tokens,"temperature":temperature,
                   "top_k":top_k,"penalty":penalty,"seed":seed},
       "input_sha256":{**{name:digest(p) for name,p in paths.items()},"tokenizer":digest(tokenizer)},
       "cases":cases,"quality_gate_run":False,"human_review_complete":False,
       "independent_holdout_verified":False,"production_promotion_allowed":False,
       "interpretation":["Teacher-forced NLL uses separately tokenized prompt/continuation boundaries, identically across models.",
        "Generated text quality remains a separate subjective and objective evaluation.",
        "These probes may overlap historical training and are not independent holdout.",
        "First-token divergence is a property of sampling/decoding, not proof of semantic change."]}
    report.parent.mkdir(parents=True,exist_ok=True)
    with report.open("x",encoding="utf-8") as f:json.dump(result,f,ensure_ascii=False,indent=2)
    return result

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--base",type=Path,default=Path("model/model-llm-try-nagato-chat-v94.pt"))
    for k in "ABC":ap.add_argument("--"+k.lower(),type=Path,default=Path(f"results/offline_replay_v0135811/candidate_{k}.pt"))
    ap.add_argument("--tokenizer",type=Path,default=Path("../LLM_GPU/model/tokenizer-v0.7-bpe.json"))
    ap.add_argument("--output",type=Path,default=Path("results/offline_generation_diagnostics_v0135813.json"))
    ap.add_argument("--max-new-tokens",type=int,default=80)
    ap.add_argument("--seed",type=int,default=135813)
    a=ap.parse_args()
    paths={"base":a.base,"A":a.a,"B":a.b,"C":a.c}
    for p in [*paths.values(),a.tokenizer]:
        if not p.is_file():ap.error("missing "+str(p))
    if len({p.resolve() for p in [*paths.values(),a.tokenizer,a.output]})!=6:
        ap.error("duplicate/overlapping input and output")
    r=run(paths,a.tokenizer,a.output,a.max_new_tokens,seed=a.seed)
    print(json.dumps({"status":r["status"],"cases":len(r["cases"]),
                      "quality_gate_run":False,"production_promotion_allowed":False}))
    print("report:",a.output)
if __name__=="__main__":main()

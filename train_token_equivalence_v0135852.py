"""v0.13.58.52: token-level equality, normalization audit, 1/4/8-item fit.

Use existing small-transformer SFT functions. Inference equality is tested in
token IDs, not only Unicode surface strings. This is an experimental memorization
test, not a generalization benchmark.
"""
import argparse,json,hashlib,random,unicodedata
from pathlib import Path
from dialogue_format_v0135817 import prompt_for,dialogue_for
from aligned_replay_examples_v0135816 import make_aligned_examples
from train_japanese_foundation_v01344 import masked_ce

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def rows(path):
    allrows=[json.loads(x) for x in path.read_text(encoding="utf-8-sig").splitlines() if x.strip()]
    data=[r for r in allrows if r["split"]=="train"]
    if len(data)<8 or len({r["user"] for r in data})!=len(data):raise ValueError("need 8 unique training prompts")
    return data
def target_ids(tok,row):
    return tok.encode(row["assistant"].strip(),add_bos=False,add_eos=True)
def predict(model,tok,row,max_new_tokens):
    prefix=tok.encode(prompt_for(row["user"]),add_bos=True)
    result=model.generate(prefix,max_new_tokens=max_new_tokens,eos_id=tok.eos_id,
                          temperature=0.0,repetition_penalty=1.0)[len(prefix):]
    if result and result[-1]==tok.eos_id:result=result[:-1]
    expected=target_ids(tok,row)
    ids=list(result)
    target_no_eos=expected[:-1] if expected[-1]==tok.eos_id else expected
    decoded=tok.decode(ids)
    canonical=tok.decode(target_no_eos)
    return {"id":row["id"],"expected_text":row["assistant"],"decoded_target":canonical,
            "generated":decoded,"raw_exact":decoded.strip()==row["assistant"].strip(),
            "token_exact_body":ids==target_no_eos,
            "decode_roundtrip_equal":canonical==row["assistant"].strip(),
            "nfkc_equal":unicodedata.normalize("NFKC",decoded)==unicodedata.normalize("NFKC",row["assistant"].strip()),
            "generated_ids":ids,"target_ids":target_no_eos}
def run(args):
    if args.output_dir.exists():raise FileExistsError(args.output_dir)
    if args.count not in (1,4,8) or not 1<=args.max_steps<=500 or args.check_every<1:raise ValueError("invalid bounds")
    chosen=rows(args.source)[:args.count]
    report={"version":"v0.13.58.52","count":args.count,"source_sha256":sha(args.source),
            "base_sha256":sha(args.base),"status":"DRY_RUN","production_approved":False,
            "generalization_evaluated":False}
    if not args.run:
        print(json.dumps(report,ensure_ascii=False,indent=2));return report
    if not args.acknowledge_experiment:raise ValueError("acknowledgement required")
    import torch
    from model import LanguageModel
    from tokenizer_bpe import Tokenizer
    random.seed(args.seed);torch.manual_seed(args.seed)
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tok=Tokenizer.load(str(args.tokenizer))
    model,_=LanguageModel.load_checkpoint(str(args.base),device=device)
    if model.vocab_size!=tok.vocab_size:raise ValueError("vocab mismatch")
    ex=make_aligned_examples([("conversation",dialogue_for(r["user"],r["assistant"])) for r in chosen],
                             tok,model.context_length,assistant_only=True)
    x,y,mask=ex.tensors
    opt=torch.optim.AdamW(model.parameters(),lr=args.lr,weight_decay=0.01)
    events=[];steps=0
    def snapshot():
        model.eval()
        with torch.inference_mode():results=[predict(model,tok,r,args.max_new_tokens) for r in chosen]
        event={"step":steps,"token_exact_count":sum(r["token_exact_body"] for r in results),
               "raw_exact_count":sum(r["raw_exact"] for r in results),
               "results":results}
        events.append(event)
        print(json.dumps({"step":steps,"token_exact_count":event["token_exact_count"],
                          "raw_exact_count":event["raw_exact_count"]},ensure_ascii=False))
        return event["token_exact_count"]==len(chosen)
    done=snapshot()
    args.output_dir.mkdir(parents=True,exist_ok=False)
    while not done and steps<args.max_steps:
        for _ in range(min(args.check_every,args.max_steps-steps)):
            model.train();opt.zero_grad(set_to_none=True)
            for i in range(len(x)):
                loss=masked_ce(model,x[i:i+1].to(device),y[i:i+1].to(device),mask[i:i+1].to(device))
                (loss/len(x)).backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(),1.0);opt.step();steps+=1
        done=snapshot()
    checkpoint=args.output_dir/"token-memorization-experimental.pt"
    model.save_checkpoint(str(checkpoint),epoch=1,metadata={"experiment":"TOKEN_EQUIVALENCE_V0135852","production_approved":False})
    report.update({"status":"ALL_TOKEN_EXACT" if done else "MAX_STEPS",
                   "steps":steps,"checkpoint":str(checkpoint),"checkpoint_sha256":sha(checkpoint),
                   "events":events})
    (args.output_dir/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return report
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,default=Path("data/daily_sft_corrected_v0135849.jsonl"))
    p.add_argument("--base",type=Path,default=Path("model/model-gpu-v1.6.2-online.pt"))
    p.add_argument("--tokenizer",type=Path,default=Path("../LLM_GPU/model/tokenizer-v0.7-bpe.json"))
    p.add_argument("--output-dir",type=Path,default=Path("results/token_equivalence_v0135852_n1"))
    p.add_argument("--count",type=int,choices=(1,4,8),default=1)
    p.add_argument("--max-steps",type=int,default=150)
    p.add_argument("--check-every",type=int,default=10)
    p.add_argument("--max-new-tokens",type=int,default=64)
    p.add_argument("--lr",type=float,default=2e-5)
    p.add_argument("--seed",type=int,default=135852)
    p.add_argument("--run",action="store_true")
    p.add_argument("--acknowledge-experiment",action="store_true")
    run(p.parse_args())
if __name__=="__main__":main()

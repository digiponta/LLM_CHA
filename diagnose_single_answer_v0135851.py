"""v0.13.58.51 One-example bounded overfit + token-by-token diagnosis.

Experimental only; no source checkpoint overwrite or automatic promotion.
Teacher-forced token ranks/probabilities and free-running greedy generations are
different measurements and both are logged.
"""
import argparse,hashlib,json,random
from pathlib import Path
from dialogue_format_v0135817 import dialogue_for,prompt_for
from aligned_replay_examples_v0135816 import make_aligned_examples
from train_japanese_foundation_v01344 import masked_ce
from train_iterative_corrective_v0135833 import generate

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def find_row(path,query):
    rows=[json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    matches=[r for r in rows if r.get("user")==query and r.get("split")=="train"]
    if len(matches)!=1:raise ValueError("expected exactly one training row for target")
    row=matches[0]
    if not row.get("assistant") or "\ufffd" in row["assistant"]:raise ValueError("invalid teacher")
    return row

def diagnostics(model,tok,row,device):
    import torch
    prefix=tok.encode(prompt_for(row["user"]),add_bos=True)
    # Match aligned_replay_examples_v0135816 exactly: encode prompt and answer separately.
    # Joint BPE tokenization of prompt+answer can change boundary tokens.
    target=tok.encode(row["assistant"].strip(),add_bos=False,add_eos=True)
    completion=prefix+target
    if not target:raise ValueError("empty completion tokens")
    if len(completion)>model.context_length:raise ValueError("context exceeded")
    trace=[]
    model.eval()
    with torch.inference_mode():
        for j,correct in enumerate(target):
            context=completion[:len(prefix)+j]
            x=torch.tensor([context],dtype=torch.long,device=device)
            logits=model(x)[0,-1,:].float()
            probs=logits.softmax(-1)
            rank=int((logits>logits[correct]).sum().item())+1
            trace.append({"index":j,"target_id":int(correct),"piece":tok.decode([int(correct)]),
                          "rank":rank,"probability":float(probs[correct].item()),
                          "top_id":int(logits.argmax().item()),
                          "top_piece":tok.decode([int(logits.argmax().item())])})
    return trace

def run(args):
    if args.output_dir.exists():raise FileExistsError(args.output_dir)
    if not 1<=args.max_steps<=1000 or not 1<=args.check_every<=args.max_steps:raise ValueError("bad step bounds")
    if args.lr<=0 or args.lr>1e-3:raise ValueError("bad learning rate")
    row=find_row(args.source,args.question)
    report={"version":"v0.13.58.51","question":row["user"],"reference":row["assistant"],
            "base_sha256":digest(args.base),"source_sha256":digest(args.source),
            "tokenizer_sha256":digest(args.tokenizer),"max_steps":args.max_steps,
            "status":"DRY_RUN","training_performed":False,"production_approved":False}
    if not args.run:
        print(json.dumps(report,ensure_ascii=False,indent=2));return report
    if not args.acknowledge_experiment:raise ValueError("--acknowledge-experiment required")
    import torch
    from model import LanguageModel
    from tokenizer_bpe import Tokenizer
    random.seed(args.seed);torch.manual_seed(args.seed)
    if torch.cuda.is_available():torch.cuda.manual_seed_all(args.seed)
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tok=Tokenizer.load(str(args.tokenizer))
    model,_=LanguageModel.load_checkpoint(str(args.base),device=device)
    if model.vocab_size!=tok.vocab_size:raise ValueError("tokenizer mismatch")
    example=make_aligned_examples([("conversation",dialogue_for(row["user"],row["assistant"]))],
        tok,model.context_length,assistant_only=True)
    x,y,mask=example.tensors
    if int(mask.sum())<=0:raise ValueError("no supervised assistant tokens")
    opt=torch.optim.AdamW(model.parameters(),lr=args.lr,weight_decay=0.01)
    args.output_dir.mkdir(parents=True,exist_ok=False)
    events=[]
    def measure(step,loss=None):
        trace=diagnostics(model,tok,row,device)
        generated=generate(model,tok,row,args.max_new_tokens)
        exact=generated.strip()==row["assistant"].strip()
        event={"step":step,"loss":loss,"generated":generated,"exact":exact,
               "target_top1_count":sum(t["rank"]==1 for t in trace),
               "target_count":len(trace),"first_mismatch":next((t for t in trace if t["rank"]!=1),None),
               "tokens":trace}
        events.append(event)
        print(json.dumps({k:event[k] for k in ("step","loss","generated","exact","target_top1_count","target_count")},ensure_ascii=False))
        return exact
    exact=measure(0)
    steps=0
    while not exact and steps<args.max_steps:
        for _ in range(min(args.check_every,args.max_steps-steps)):
            model.train();opt.zero_grad(set_to_none=True)
            loss=masked_ce(model,x.to(device),y.to(device),mask.to(device))
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(),1.0)
            opt.step();steps+=1
        exact=measure(steps,float(loss.detach().cpu()))
    ckpt=args.output_dir/"single-answer-experimental.pt"
    model.save_checkpoint(str(ckpt),epoch=1,loss=events[-1]["loss"],
        metadata={"experiment":"SINGLE_ANSWER_TOKEN_DIAGNOSTIC_V0135851","production_approved":False})
    report.update({"status":"EXACT_GENERATION_REACHED" if exact else "MAX_STEPS_WITHOUT_EXACT_GENERATION",
                   "training_performed":steps>0,"steps":steps,"checkpoint":str(ckpt),
                   "checkpoint_sha256":digest(ckpt),"events":events})
    (args.output_dir/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,default=Path("data/daily_sft_corrected_v0135849.jsonl"))
    p.add_argument("--question",default="最近ちょっと眠たい")
    p.add_argument("--base",type=Path,default=Path("model/model-gpu-v1.6.2-online.pt"))
    p.add_argument("--tokenizer",type=Path,default=Path("../LLM_GPU/model/tokenizer-v0.7-bpe.json"))
    p.add_argument("--output-dir",type=Path,default=Path("results/single_answer_v0135851"))
    p.add_argument("--max-steps",type=int,default=150)
    p.add_argument("--check-every",type=int,default=10)
    p.add_argument("--max-new-tokens",type=int,default=64)
    p.add_argument("--lr",type=float,default=2e-5)
    p.add_argument("--seed",type=int,default=135851)
    p.add_argument("--run",action="store_true")
    p.add_argument("--acknowledge-experiment",action="store_true")
    run(p.parse_args())
if __name__=="__main__":main()

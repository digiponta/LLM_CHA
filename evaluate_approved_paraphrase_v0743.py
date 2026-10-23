"""Read-only comparison of exact, train-form and holdout-form generation."""
import argparse,json
from pathlib import Path
from approved_semantic_sleep_v0740 import _load_jsonl
from verify_trusted_generation_v0742 import perform,summarize,_sha

def probes(data):
    out=[]
    for split in ("train","holdout"):
        for row in data[split]:
            out.append({"group":split,"question":row["question"],
                        "expected_answer":row["answer"],"approved_id":row["approved_id"]})
    return out

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--dataset",default="results/approved_paraphrase_v0743.json")
    p.add_argument("--model",default="model/model-gpu-v1.6.2-online.pt")
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--output",default="results/approved_paraphrase_eval_v0743.json")
    args=p.parse_args()
    from model import LanguageModel
    from tokenizer_bpe import Tokenizer
    import torch
    paths=[Path(x).resolve() for x in (args.dataset,args.model,args.tokenizer)]
    if Path(args.output).resolve() in paths:raise ValueError("output overlaps input")
    before={str(x):_sha(x) for x in paths}
    data=json.loads(Path(args.dataset).read_text(encoding="utf-8"))
    model,_=LanguageModel.load_checkpoint(args.model,device=torch.device("cuda" if torch.cuda.is_available() else "cpu"))
    tok=Tokenizer.load(args.tokenizer)
    cases=perform(model,tok,probes(data))
    if before!={str(x):_sha(x) for x in paths}:raise RuntimeError("protected inputs changed")
    report={"version":"v0.7.43","scope":"MODEL_ONLY_GREEDY","trained_this_run":False,
            "summary":summarize(cases),"cases":cases}
    out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report["summary"],ensure_ascii=False,indent=2))
    print("report:",out)
if __name__=="__main__":main()

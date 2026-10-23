"""v0.7.43 opt-in isolated fine-tune on train split only.

Never overwrite Trusted production checkpoint, state, or chat history.
Requires local CUDA training environment to execute.
"""
import argparse,json,subprocess,sys
from pathlib import Path

def training_rows(dataset):
    return [{"user":r["question"],"assistant":r["answer"],"source":"semantic-sleep",
             "approved_id":r["approved_id"]}
            for r in dataset["train"]]

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--dataset",default="results/approved_paraphrase_v0743.json")
    p.add_argument("--base",default="model/model-gpu-v1.6.2-online.pt")
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--output",default="results/approved_paraphrase_v0743/experimental-trusted.pt")
    p.add_argument("--state",default="results/approved_paraphrase_v0743/learning_state.json")
    p.add_argument("--train-log",default="results/approved_paraphrase_v0743/train.jsonl")
    args=p.parse_args()
    data=json.loads(Path(args.dataset).read_text(encoding="utf-8"))
    rows=training_rows(data)
    if not rows:raise ValueError("no approved source-evidence training examples")
    for path in (args.output,args.state,args.train_log):
        if Path(path).resolve() in {Path(args.base).resolve(),Path(args.tokenizer).resolve(),
                                    Path(args.dataset).resolve()}:
            raise ValueError("training output overlaps protected input")
    if Path(args.output).exists() or Path(args.state).exists() or Path(args.train_log).exists():
        raise FileExistsError("experiment outputs exist; use a fresh output directory")
    if len({Path(x).resolve() for x in (args.output,args.state,args.train_log)})!=3:
        raise ValueError("training outputs must be distinct")
    log=Path(args.train_log);log.parent.mkdir(parents=True,exist_ok=True)
    log.write_text("".join(json.dumps(row,ensure_ascii=False)+"\n" for row in rows),encoding="utf-8")
    cmd=[sys.executable,"online_train.py","--chat-data",str(log),
         "--base-model",args.base,"--tokenizer",args.tokenizer,
         "--output",args.output,"--state",args.state]
    print("TRAIN_ONLY:",len(rows),"HOLDOUT:",len(data["holdout"]))
    print("Isolated command:",subprocess.list2cmdline(cmd),flush=True)
    subprocess.run(cmd,check=True)
if __name__=="__main__":main()

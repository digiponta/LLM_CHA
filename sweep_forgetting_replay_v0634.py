"""v0.6.34: isolated sweep for forgetting-aware online learning.

Candidates are experimental and never promoted automatically.
"""
import argparse
import hashlib
import itertools
import json
import subprocess
import sys
from pathlib import Path

def sweep(base, tokenizer, chat, replay, stability, cases, out_dir, learning_rates, epochs, stability_weights):
    paths=[base,tokenizer,chat,stability,cases]
    missing=[str(p) for p in paths if not Path(p).is_file()]
    if missing:raise FileNotFoundError("Missing required inputs: "+", ".join(missing))
    out=Path(out_dir)
    out.mkdir(parents=True,exist_ok=True)
    original=hashlib.sha256(Path(base).read_bytes()).hexdigest()
    results=[]
    for lr,epoch,weight in itertools.product(learning_rates,epochs,stability_weights):
        label="lr{}_e{}_sw{}".format(str(lr).replace(".","p").replace("-","m"),epoch,weight)
        model=out/(label+".pt")
        state=out/(label+".state.json")
        report=out/(label+".quality.json")
        train_cmd=[sys.executable,"online_train.py","--chat-data",str(chat),
            "--base-model",str(base),"--tokenizer",str(tokenizer),
            "--output",str(model),"--state",str(state),
            "--epochs",str(epoch),"--learning-rate",str(lr),
            "--stability-data",str(stability),"--stability-weight",str(weight),
            "--replay-data",str(replay),"--tiny-threshold","10"]
        training=subprocess.run(train_cmd,capture_output=True,text=True,encoding="utf-8",errors="replace")
        item={"candidate":label,"model":str(model),"training_returncode":training.returncode,
              "training_tail":training.stdout[-1400:],"training_error":training.stderr[-800:]}
        if training.returncode==0 and model.is_file():
            quality_cmd=[sys.executable,"evaluate_online_quality_v0632.py",
                "--before",str(base),"--after",str(model),
                "--tokenizer",str(tokenizer),"--cases",str(cases),
                "--output",str(report)]
            quality=subprocess.run(quality_cmd,capture_output=True,text=True,encoding="utf-8",errors="replace")
            item["quality_returncode"]=quality.returncode
            if report.is_file():
                q=json.loads(report.read_text(encoding="utf-8"))
                item["quality_pass"]=bool(q.get("pass"))
                item["forgetting_rate"]=q.get("forgetting_rate")
                item["new_accuracy"]=q.get("new_accuracy")
                item["quality_regressions"]=q.get("response_quality_v0633",{}).get("quality_regressions",[])
            else:
                item["quality_pass"]=False
                item["quality_error"]=quality.stderr[-800:]
        else:
            item["quality_pass"]=False
        results.append(item)
        # Audit report survives interruption; no production model/state writes.
        (out/"sweep_results.json").write_text(json.dumps(
            {"runs":results,"accepted_candidates":[r["candidate"] for r in results if r["quality_pass"]],
             "auto_promote":False},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        if hashlib.sha256(Path(base).read_bytes()).hexdigest()!=original:
            raise RuntimeError("Baseline model unexpectedly modified")
    return results

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--base",default="model/model-gpu-v1.6.2-online.pt")
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--chat",default="data/quality_training_v0632.jsonl")
    p.add_argument("--replay",default="data/conversation-ja.txt")
    p.add_argument("--stability",default="data/stability_replay_v104.jsonl")
    p.add_argument("--cases",default="data/quality_cases_v0632.example.json")
    p.add_argument("--output-dir",default="results/quality_sweep_v0634")
    p.add_argument("--learning-rates",default="1e-5,3e-6")
    p.add_argument("--epochs",default="3,8")
    p.add_argument("--stability-weights",default="1,4")
    a=p.parse_args()
    r=sweep(a.base,a.tokenizer,a.chat,a.replay,a.stability,a.cases,
        a.output_dir,[float(x) for x in a.learning_rates.split(",")],
        [int(x) for x in a.epochs.split(",")],
        [int(x) for x in a.stability_weights.split(",")])
    print(json.dumps({"runs":len(r),"passed":sum(x["quality_pass"] for x in r),
        "report":str(Path(a.output_dir)/"sweep_results.json")},ensure_ascii=False))
if __name__=="__main__":main()

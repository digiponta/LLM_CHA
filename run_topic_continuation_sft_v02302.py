"""Run matched continuation SFT with validated training rows."""
import argparse,subprocess,sys,json
from pathlib import Path
from prepare_topic_continuation_v02302 import build,validate
from train_nagato_chat import load_pairs

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--context",default="data/topic_continuation_v02302/train_preformatted.jsonl")
    p.add_argument("--output",default="model/model-llm-cha-topic-continuation-v02302.pt")
    p.add_argument("--dry-run",action="store_true")
    a=p.parse_args()
    if not Path(a.context).is_file():p.error("run prepare_topic_continuation_v02302.py first")
    expected=build();validate(expected)
    actual=[{"user":user,"assistant":answer} for user,answer in load_pairs(Path(a.context))]
    if actual!=expected:p.error("training data mismatches expected, re-run preparation")
    print("Validated continuation rows: 12/12",flush=True)
    cmd=[sys.executable,"run_topic_grounded_sft_v02291.py","--context",a.context,
         "--output",a.output,"--context-weight","18"]
    if a.dry_run:cmd.append("--dry-run")
    print("Command:",subprocess.list2cmdline(cmd),flush=True)
    subprocess.run(cmd,check=True)
if __name__=="__main__":main()

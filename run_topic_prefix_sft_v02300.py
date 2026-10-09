"""Run matched topic-prefix SFT using the validated v0.2.29.1 launcher."""
import argparse,subprocess,sys
from pathlib import Path

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--context",default="data/topic_prefix_v02300/train_preformatted.jsonl")
    p.add_argument("--output",default="model/model-llm-cha-topic-prefix-v02300.pt")
    p.add_argument("--dry-run",action="store_true")
    a=p.parse_args()
    if not Path(a.context).is_file():
        p.error("Run python prepare_topic_prefix_v02300.py first")
    cmd=[sys.executable,"run_topic_grounded_sft_v02291.py",
         "--context",a.context,"--output",a.output,
         "--context-weight","18"]
    if a.dry_run:cmd.append("--dry-run")
    print("Command:",subprocess.list2cmdline(cmd),flush=True)
    subprocess.run(cmd,check=True)
if __name__=="__main__":main()

"""v0.2.30.4 recovery SFT runner with data integrity check."""
import argparse,subprocess,sys
from pathlib import Path
from train_nagato_chat import load_pairs
from prepare_prefix_recovery_v02304 import build

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--context",default="data/prefix_recovery_v02304/train_preformatted.jsonl")
    p.add_argument("--output",default="model/model-llm-cha-prefix-recovery-v02304.pt")
    p.add_argument("--dry-run",action="store_true")
    a=p.parse_args()
    path=Path(a.context)
    if not path.is_file():p.error("Run prepare_prefix_recovery_v02304.py first")
    expected=[(r["user"],r["assistant"]) for r in build()]
    if load_pairs(path)!=expected:p.error("Recovery data differs from audited rows; regenerate")
    print("Validated recovery: continue=6 restart=6 total=12",flush=True)
    cmd=[sys.executable,"run_topic_grounded_sft_v02291.py",
         "--context",a.context,"--output",a.output,"--context-weight","18"]
    if a.dry_run:cmd.append("--dry-run")
    print("Command:",subprocess.list2cmdline(cmd),flush=True)
    subprocess.run(cmd,check=True)
if __name__=="__main__":main()

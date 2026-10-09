"""v0.2.30.1 guarded launch; same training setup as v0.2.29.1."""
import argparse,subprocess,sys
from pathlib import Path
from prepare_topic_prefix_v02301 import build
from train_nagato_chat import load_pairs

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",default="data/topic_grounded_v02290/train.jsonl")
    p.add_argument("--context",default="data/topic_prefix_v02301/train_preformatted.jsonl")
    p.add_argument("--output",default="model/model-llm-cha-topic-prefix-v02301.pt")
    p.add_argument("--dry-run",action="store_true")
    a=p.parse_args()
    if not Path(a.source).is_file():p.error("run prepare_topic_grounded_v02290.py first")
    if not Path(a.context).is_file():p.error("run prepare_topic_prefix_v02301.py first")
    import json
    old=[json.loads(s) for s in Path(a.source).read_text(encoding="utf-8-sig").splitlines() if s.strip()]
    expected,changed=build(old)
    actual=[{"user":u,"assistant":v} for u,v in load_pairs(Path(a.context))]
    if actual!=expected:p.error("generated training rows differ from validated 12/12 changed data; re-run preparation")
    print(f"Validated topic prefix changes: {changed}/12",flush=True)
    cmd=[sys.executable,"run_topic_grounded_sft_v02291.py",
         "--context",a.context,"--output",a.output,"--context-weight","18"]
    if a.dry_run:cmd.append("--dry-run")
    print("Command:",subprocess.list2cmdline(cmd),flush=True)
    subprocess.run(cmd,check=True)
if __name__=="__main__":main()

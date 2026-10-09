"""v0.2.29.1 controlled Topic-Grounded SFT from the same base checkpoint."""
import argparse,subprocess,json
from train_nagato_chat import load_pairs
from pathlib import Path
from train_context_weighted_v0224 import command

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--train",default="data/context_generalization_v0225/train.jsonl")
    p.add_argument("--context",default="data/topic_grounded_v02290/train_preformatted.jsonl")
    p.add_argument("--val",default="data/context_generalization_v0225/val.jsonl")
    p.add_argument("--manifest",default="data/context_generalization_v0225/manifest.json")
    p.add_argument("--anchors",default="data/realpersonachat_quality/persona_anchors_preformatted.jsonl")
    p.add_argument("--base-model",default="model/model-llm-cha-response-quality-v0221.pt")
    p.add_argument("--tokenizer",default="../LLM_TRY/model/tokenizer-v0.7-bpe.json")
    p.add_argument("--output",default="model/model-llm-cha-topic-grounded-v02291.pt")
    p.add_argument("--context-weight",type=int,default=18)
    p.add_argument("--anchor-weight",type=int,default=10)
    p.add_argument("--epochs",type=int,default=3)
    p.add_argument("--batch-size",type=int,default=8)
    p.add_argument("--learning-rate",type=float,default=2e-6)
    p.add_argument("--lm-head-learning-rate",type=float,default=3e-7)
    p.add_argument("--init-k",type=int,default=8)
    p.add_argument("--init-weight",type=float,default=0.5)
    p.add_argument("--late-weight",type=float,default=0.5)
    p.add_argument("--dry-run",action="store_true")
    a=p.parse_args()
    if a.init_k<1 or not 0<=a.init_weight<=10 or not 0<=a.late_weight<=10:p.error("invalid loss arguments")
    if not Path(a.context).is_file():p.error("run prepare_topic_grounded_preformatted_v02291.py first")
    # Historical manifest: 18 context rows x 12 = 216 exposures.
    # New experiment: 12 grounded rows x 18 = 216 exposures.
    context_count = len(load_pairs(Path(a.context)))
    if context_count != 12 or a.context_weight != 18:
        p.error("v0.2.29.1 expects 12 grounded rows at weight 18")
    old_manifest = json.loads(Path(a.manifest).read_text(encoding="utf-8"))
    old_exposures = old_manifest["unique_context_pairs"] * old_manifest["context_weight"]
    if old_exposures != context_count * a.context_weight:
        p.error("Context exposure counts differ from historical experiment")

    # Retain upstream manifest validation using an experiment-local compatible copy.
    import tempfile
    with tempfile.TemporaryDirectory(prefix="llm_cha_v02291_") as tmp:
        manifest_path = Path(tmp) / "manifest.json"
        new_manifest = dict(old_manifest, unique_context_pairs=context_count,
                            context_weight=a.context_weight)
        manifest_path.write_text(json.dumps(new_manifest, ensure_ascii=False), encoding="utf-8")
        a.manifest = str(manifest_path)
        cmd, stats = command(a)

    if cmd[1]!="train_nagato_chat.py":raise RuntimeError("unexpected upstream trainer")
    cmd[1]="train_context_persistence_v0228.py"
    cmd+=["--context-selective","--init-k",str(a.init_k),
          "--init-weight",str(a.init_weight),"--late-weight",str(a.late_weight)]
    print("Exposures:",json.dumps(stats,ensure_ascii=False),flush=True)
    print("Command:",subprocess.list2cmdline(cmd),flush=True)
    if not a.dry_run:subprocess.run(cmd,check=True)
if __name__=="__main__":main()

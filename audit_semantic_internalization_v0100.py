"""Read-only audit of Nagato /sleep internalization fingerprint accounting."""
import argparse
import json
from pathlib import Path
from internalized_knowledge_v10100 import load_trained_fingerprints
from semantic_sleep_learning_v10131 import load_nagato_semantic_memory

def audit(semantic_memory_path, learning_state_path, checkpoint_fingerprints):
    rows=load_nagato_semantic_memory(Path(semantic_memory_path))
    memory={str(x.get("fingerprint","")) for x in rows if x.get("fingerprint")}
    learned=set(load_trained_fingerprints(Path(learning_state_path)))
    checkpoint=set(str(x) for x in checkpoint_fingerprints)
    both=learned & checkpoint
    effective=memory & both
    if not learned:
        reason="LEARNING_STATE_HAS_NO_TRAINED_FINGERPRINTS"
    elif not checkpoint:
        reason="CHECKPOINT_HAS_NO_TRAINED_FINGERPRINTS"
    elif not (learned & checkpoint):
        reason="NO_SHARED_LEARNING_CHECKPOINT_FINGERPRINTS"
    elif not effective:
        reason="MEMORY_FINGERPRINTS_NOT_IN_BOTH"
    else:
        reason="SHARED_FINGERPRINTS_PRESENT"
    return {
        "status":reason,
        "memory_rows":len(rows),
        "memory_unique_fingerprints":len(memory),
        "learning_state_count":len(learned),
        "checkpoint_count":len(checkpoint),
        "learning_checkpoint_shared":len(both),
        "memory_in_learning_state":len(memory & learned),
        "memory_in_checkpoint":len(memory & checkpoint),
        "internalized_reported_by_intersection":len(effective),
        "pending_reported_by_intersection":len(rows)-sum(1 for r in rows if str(r.get("fingerprint","")) in both),
        "checkpoint_weights_verified":False,
        "read_only":True,
    }

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--memory",required=True,type=Path)
    parser.add_argument("--learning-state",required=True,type=Path)
    parser.add_argument("--checkpoint-fingerprints-json",required=True,type=Path,
                        help="JSON list exported from the loaded checkpoint's metadata.trained_fingerprints")
    args=parser.parse_args()
    fingerprints=json.loads(args.checkpoint_fingerprints_json.read_text(encoding="utf-8-sig"))
    if not isinstance(fingerprints,list):
        parser.error("checkpoint-fingerprints-json must contain a JSON array")
    print(json.dumps(audit(args.memory,args.learning_state,fingerprints),ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()

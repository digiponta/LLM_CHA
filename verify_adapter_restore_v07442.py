"""v0.7.44.2: read-only real model load + checkpoint/state fingerprint audit."""
import argparse
import json
from pathlib import Path
from diagnose_adapter_restore_v07441 import diagnose


def verify(checkpoint, state=None, device="cpu"):
    pre = diagnose(checkpoint, state=state)
    result = {"version":"v0.7.44.2","preflight":pre,
              "runtime_restore_verified":False,"status":"FAILED","reason":pre["reason"],
              "fingerprints":None,"generation_verified":False}
    if pre["restore_status"] != "PREFLIGHT_OK":
        return result
    try:
        import torch
        from model import LanguageModel
        model, payload = LanguageModel.load_checkpoint(str(checkpoint), device=torch.device(device))
        model.eval()
    except Exception as e:
        result["reason"] = "MODEL_RESTORE_FAILED"
        result["error_type"] = type(e).__name__
        result["error_message"] = str(e)[:600]
        return result
    result["runtime_restore_verified"] = True
    metadata = payload.get("metadata", {})
    if not isinstance(metadata, dict):
        result["reason"] = "INVALID_METADATA"
        return result
    checkpoint_values = metadata.get("trained_fingerprints", [])
    if not isinstance(checkpoint_values, (list, tuple, set)):
        result["reason"] = "INVALID_CHECKPOINT_FINGERPRINTS"
        return result
    checkpoint_fps = {str(v) for v in checkpoint_values}
    if state:
        try:
            state_payload = json.loads(Path(state).read_text(encoding="utf-8"))
            state_values = state_payload.get("trained_fingerprints", [])
            if not isinstance(state_values, list):
                raise ValueError("invalid trained_fingerprints")
            state_fps = {str(v) for v in state_values}
        except (OSError, ValueError, AttributeError, TypeError) as e:
            result["reason"] = "INVALID_STATE_FINGERPRINTS"
            result["error_type"] = type(e).__name__
            return result
        result["fingerprints"] = {
            "checkpoint_count":len(checkpoint_fps),
            "state_count":len(state_fps),
            "checkpoint_only":sorted(checkpoint_fps-state_fps),
            "state_only":sorted(state_fps-checkpoint_fps),
        }
        if checkpoint_fps != state_fps:
            result["reason"] = "FINGERPRINT_MISMATCH"
            return result
    result["status"] = "RESTORE_OK"
    result["reason"] = "MODEL_LOADED_AND_BINDINGS_CHECKED" if state else "MODEL_LOADED_STATE_NOT_CHECKED"
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--checkpoint",default="results/approved_paraphrase_v0743/experimental-trusted.pt")
    p.add_argument("--state",default="results/approved_paraphrase_v0743/learning_state.json")
    p.add_argument("--device",choices=("cpu","cuda"),default="cpu")
    p.add_argument("--output",default="results/restore_diagnostic_v07442.json")
    args=p.parse_args()
    protected={Path(x).resolve() for x in (args.checkpoint,args.state)}
    if Path(args.output).resolve() in protected:
        p.error("output overlaps protected input")
    result=verify(args.checkpoint,args.state,args.device)
    data=json.dumps(result,ensure_ascii=False,indent=2)+"\\n"
    out=Path(args.output)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(data,encoding="utf-8")
    print(data)
    return 0 if result["status"]=="RESTORE_OK" else 1

if __name__=="__main__":
    raise SystemExit(main())

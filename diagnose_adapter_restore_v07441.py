"""LLM_CHA v0.7.44.1: read-only checkpoint / adapter restore preflight.

A preflight success is NOT evidence that runtime adapter restore or generated
responses succeed. Never writes model, state, ledger or candidate files.
"""
import argparse
import json
from pathlib import Path


def diagnose(checkpoint, *, state=None, approved=None, candidates=None, load_payload=True):
    p = Path(checkpoint)
    result = {
        "version": "v0.7.44.1",
        "checkpoint": str(p),
        "restore_status": "FAILED",
        "reason": None,
        "checks": {},
        "runtime_restore_verified": False,
        "protected_inputs_modified": False,
    }

    def fail(reason):
        result["reason"] = reason
        return result

    if not p.is_file():
        result["checks"]["checkpoint_exists"] = False
        return fail("CHECKPOINT_NOT_FOUND")
    result["checks"]["checkpoint_exists"] = True
    try:
        with p.open("rb") as f:
            prefix = f.read(16)
        if not prefix:
            return fail("CHECKPOINT_CORRUPT")
    except OSError as exc:
        result["checks"]["read_error"] = type(exc).__name__
        return fail("CHECKPOINT_UNREADABLE")

    for name, location in (("state", state), ("approved", approved), ("candidates", candidates)):
        if location is None:
            result["checks"][name] = "NOT_REQUESTED"
            continue
        target = Path(location)
        if not target.is_file():
            result["checks"][name] = "MISSING"
            return fail("SEMANTIC_STATE_MISMATCH")
        try:
            if target.suffix.lower() == ".json":
                parsed = json.loads(target.read_text(encoding="utf-8"))
                if not isinstance(parsed, (dict, list)):
                    return fail("SEMANTIC_STATE_MISMATCH")
            elif target.suffix.lower() == ".jsonl":
                with target.open(encoding="utf-8") as f:
                    for line in f:
                        if line.strip() and not isinstance(json.loads(line), dict):
                            return fail("SEMANTIC_STATE_MISMATCH")
            else:
                # Unknown serialization: only check read access, do not assume format.
                with target.open("rb") as f:
                    f.read(1)
        except (OSError, UnicodeError, ValueError) as exc:
            result["checks"][name] = type(exc).__name__
            return fail("SEMANTIC_STATE_MISMATCH")
        result["checks"][name] = "READABLE"
    if not load_payload:
        result["restore_status"] = "PREFLIGHT_ONLY"
        result["reason"] = "PAYLOAD_NOT_INSPECTED"
        return result

    try:
        import torch
    except ImportError:
        return fail("TORCH_UNAVAILABLE")
    try:
        # Do not execute arbitrary pickle objects from an untrusted checkpoint.
        payload = torch.load(str(p), map_location="cpu", weights_only=True)
    except (OSError, EOFError, RuntimeError, ValueError, TypeError, KeyError, ImportError) as exc:
        result["checks"]["payload_error"] = type(exc).__name__
        return fail("CHECKPOINT_CORRUPT")
    except Exception as exc:
        # Legacy checkpoints may need an unsafe pickle loader; never use it here.
        result["checks"]["payload_error"] = type(exc).__name__
        return fail("CHECKPOINT_UNREADABLE")

    if not isinstance(payload, dict):
        return fail("SCHEMA_MISMATCH")
    result["checks"]["payload_keys"] = sorted(str(k) for k in payload.keys())
    weights = payload.get("model_state_dict", payload.get("model_state"))
    if weights is None:
        weights = payload.get("state_dict")
    if not isinstance(weights, dict) or not weights:
        return fail("SCHEMA_MISMATCH")
    if any(not isinstance(k, str) or not torch.is_tensor(v) for k, v in weights.items()):
        return fail("MODEL_INCOMPATIBLE")
    result["checks"]["tensor_count"] = len(weights)
    config = payload.get("config")
    expected = ("vocab_size", "d_model", "num_layers", "hidden_dim")
    if not isinstance(config, dict) or any(k not in config for k in expected):
        return fail("SCHEMA_MISMATCH")
    try:
        if any(int(config[k]) <= 0 for k in expected):
            return fail("MODEL_INCOMPATIBLE")
    except (TypeError, ValueError, OverflowError):
        return fail("MODEL_INCOMPATIBLE")
    result["checks"]["config"] = {k: config[k] for k in expected}
    # Validation of architecture needs the actual LanguageModel loader, not only tensor shapes.
    result["restore_status"] = "PREFLIGHT_OK"
    result["reason"] = "RUNTIME_RESTORE_NOT_TESTED"
    return result


def main():
    parser = argparse.ArgumentParser(description="Read-only Experimental Adapter checkpoint preflight")
    parser.add_argument("--checkpoint", default="results/approved_paraphrase_v0743/experimental-trusted.pt")
    parser.add_argument("--state")
    parser.add_argument("--approved")
    parser.add_argument("--candidates")
    parser.add_argument("--metadata-only", action="store_true")
    parser.add_argument("--output", help="Optional separate JSON diagnostic report")
    args = parser.parse_args()
    inputs = {Path(x).resolve() for x in (args.checkpoint, args.state, args.approved, args.candidates) if x}
    if args.output and Path(args.output).resolve() in inputs:
        parser.error("--output must not overlap protected input")
    result = diagnose(args.checkpoint, state=args.state, approved=args.approved,
                      candidates=args.candidates, load_payload=not args.metadata_only)
    data = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(data, encoding="utf-8")
    print(data, end="")
    return 0 if result["restore_status"] in ("PREFLIGHT_OK", "PREFLIGHT_ONLY") else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""CLI diagnostics for pasted startup status without mutating checkpoints."""
import argparse
import json
from pathlib import Path
from semantic_memory_status_v09766 import parse_memory_status

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--log", type=Path, help="UTF-8 text log containing the startup message")
    p.add_argument("--line", help="Single [Nagato Semantic Memory: ...] status line")
    args=p.parse_args()
    if args.line is not None:
        lines=args.line.splitlines()
    elif args.log:
        lines=args.log.read_text(encoding="utf-8-sig").splitlines()
    else:
        p.error("provide --line or --log")
    records=[r for line in lines if (r:=parse_memory_status(line)) is not None]
    if not records:
        print(json.dumps({"status":"NO_MEMORY_STATUS_FOUND"},ensure_ascii=False))
        raise SystemExit(1)
    print(json.dumps({"observations":len(records),"latest":records[-1],
                      "caution":"No checkpoint files or neural weights were inspected."},
                     ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()

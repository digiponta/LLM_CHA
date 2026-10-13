"""v0.4.28 isolated checkpoint snapshot and paired response audit.

Never invokes training, /sleep, model loading, or production promotion.
"""
import argparse
import hashlib
import json
import shutil
from pathlib import Path
from sleep_baseline_audit_v0427 import compare
from persona_quality_annotation_v0423 import load_jsonl

def digest(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda:stream.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()

def snapshot(source,destination):
    src=Path(source)
    dst=Path(destination)
    if not src.is_file() or src.is_symlink() or dst.exists() or dst.is_symlink():
        raise ValueError("source must be an existing regular file and destination must be unused")
    if src.resolve()==dst.resolve():
        raise ValueError("cannot snapshot onto original")
    dst.parent.mkdir(parents=True,exist_ok=True)
    try:
        with src.open("rb") as inp,dst.open("xb") as out:
            shutil.copyfileobj(inp,out,1024*1024)
        src_hash=digest(src)
        copy_hash=digest(dst)
        if src_hash!=copy_hash:
            raise ValueError("snapshot checksum mismatch")
        return {"source":str(src),"snapshot":str(dst),"sha256":copy_hash,
                "source_sha256":src_hash,"verified":True}
    except Exception:
        if dst.exists():dst.unlink()
        raise

def report(before_checkpoint,after_checkpoint,before_capture,after_capture):
    sources=[Path(x) for x in (before_checkpoint,after_checkpoint,before_capture,after_capture)]
    if any(not x.is_file() or x.is_symlink() for x in sources):
        raise ValueError("missing or symlink input")
    before=load_jsonl(before_capture)
    after=load_jsonl(after_capture)
    result=compare(before,after)
    return {"version":"v0.4.28","mode":"READ_ONLY_CANDIDATE_AUDIT",
            "before_checkpoint_sha256":digest(before_checkpoint),
            "after_checkpoint_sha256":digest(after_checkpoint),
            "before_capture_sha256":digest(before_capture),
            "after_capture_sha256":digest(after_capture),
            "checkpoint_bytes_differ":digest(before_checkpoint)!=digest(after_checkpoint),
            "comparison":result,
            "candidate_adopted":False,"training_executed":False,
            "quality_improvement_claimed":False,
            "independent_holdout_claimed":False}

def main():
    p=argparse.ArgumentParser()
    sub=p.add_subparsers(dest="action",required=True)
    s=sub.add_parser("snapshot");s.add_argument("--source",required=True);s.add_argument("--destination",required=True)
    c=sub.add_parser("compare")
    for name in ("before-checkpoint","after-checkpoint","before-capture","after-capture","report"):
        c.add_argument("--"+name,required=True)
    a=p.parse_args()
    try:
        if a.action=="snapshot":
            result=snapshot(a.source,a.destination)
        else:
            result=report(a.before_checkpoint,a.after_checkpoint,a.before_capture,a.after_capture)
            path=Path(a.report)
            if path.exists() or path.is_symlink():raise ValueError("report already exists; do not overwrite evidence")
            path.parent.mkdir(parents=True,exist_ok=True)
            with path.open("x",encoding="utf-8") as f:
                json.dump(result,f,ensure_ascii=False,indent=2)
                f.write("\n")
        print(json.dumps({k:v for k,v in result.items() if k!="comparison"},ensure_ascii=False,indent=2))
    except (OSError,ValueError,KeyError,TypeError) as e:
        p.exit(1,"safe sleep runner failed: "+str(e)+"\n")
if __name__=="__main__":main()

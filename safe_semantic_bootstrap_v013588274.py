"""Fail-closed bootstrap for missing semantic stores; existing unified data is immutable."""
import argparse,hashlib,json,os,tempfile
from pathlib import Path
from safe_semantic_registration_v013588273 import store_status,STORES

def assess(paths):
    states=store_status(paths)
    unified=states["unified"]
    if unified["status"]!="SOURCE_PRESENT":
        return {"status":"BLOCKED_UNIFIED_NOT_VALID","stores":states,"to_initialize":[]}
    resolved=[str(Path(paths[k]).resolve()) for k in STORES]
    if len(set(resolved))!=len(resolved):
        return {"status":"BLOCKED_OVERLAPPING_PATHS","stores":states,"to_initialize":[]}
    if any(x["status"]=="SOURCE_UNREADABLE" for x in states.values()):
        return {"status":"BLOCKED_UNREADABLE_STORE","stores":states,"to_initialize":[]}
    create=[k for k in STORES if k!="unified" and states[k]["status"]=="SOURCE_NOT_FOUND"]
    return {"status":"BOOTSTRAP_READY","stores":states,"to_initialize":create,
            "unified_sha256":hashlib.sha256(Path(paths["unified"]).read_bytes()).hexdigest()}

def initialize(paths,commit=False,backup=None):
    check=assess(paths)
    check["changed"]=False
    if not commit or check["status"]!="BOOTSTRAP_READY":return check
    unified=Path(paths["unified"])
    backup=Path(backup) if backup else unified.with_suffix(unified.suffix+".bootstrap-v013588274.bak")
    if backup.exists():raise ValueError("BACKUP_ALREADY_EXISTS")
    backup.parent.mkdir(parents=True,exist_ok=True)
    raw=unified.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=check["unified_sha256"]:
        raise ValueError("UNIFIED_CHANGED_DURING_BOOTSTRAP")
    created=[]
    try:
        with backup.open("xb") as f:
            f.write(raw);f.flush();os.fsync(f.fileno())
        for name in check["to_initialize"]:
            p=Path(paths[name])
            if not p.parent.is_dir():
                raise ValueError("STORE_DIRECTORY_NOT_FOUND: "+str(p.parent))
            with p.open("xb") as f:
                f.flush();os.fsync(f.fileno())
            created.append(p)
        if hashlib.sha256(unified.read_bytes()).hexdigest()!=check["unified_sha256"]:
            raise RuntimeError("UNIFIED_CHANGED_DURING_BOOTSTRAP")
    except Exception:
        for path in created:path.unlink()
        raise
    check["changed"]=bool(created)
    check["created"]=[str(x) for x in created]
    check["backup"]=str(backup)
    check["status"]="BOOTSTRAP_COMPLETE"
    check["stores_after"]=store_status(paths)
    return check

def main():
    p=argparse.ArgumentParser()
    for name in STORES:p.add_argument("--"+name.replace("_","-"),required=True)
    p.add_argument("--commit",action="store_true")
    p.add_argument("--backup")
    p.add_argument("--output",default="results/semantic_bootstrap_v013588274.json")
    a=p.parse_args()
    paths={name:getattr(a,name) for name in STORES}
    result=initialize(paths,commit=a.commit,backup=a.backup)
    out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],"to_initialize":result.get("to_initialize",[]),
                      "changed":result.get("changed",False),"report":str(out)},ensure_ascii=False))
if __name__=="__main__":main()

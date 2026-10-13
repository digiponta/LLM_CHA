"""v0.4.28.3 opt-in isolated chat benchmark transcript capture.

Runs cloned *source and data* in a temporary workspace; real project is not
cwd, and no training commands are sent. Human review required.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

SKIP={".git","model","results","__pycache__",".venv","venv","node_modules"}
def sha(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):h.update(block)
    return h.hexdigest()

def validate(manifest):
    if manifest.get("count")!=64 or len(manifest.get("groups",[]))!=56:
        raise ValueError("manifest must contain 64 prompts in 56 groups")
    ids=set();tot=0
    for g in manifest["groups"]:
        ident=g.get("id"); prompts=g.get("prompts")
        if not isinstance(ident,str) or ident in ids:raise ValueError("duplicate/invalid ID")
        ids.add(ident)
        if g.get("mode") not in ("SINGLE","MULTI") or not isinstance(prompts,list):
            raise ValueError("invalid group")
        if len(prompts)!=(1 if g["mode"]=="SINGLE" else 3):
            raise ValueError("invalid prompt count")
        if any(not isinstance(p,str) or not p.strip() or "\n" in p or p.lstrip().startswith(("#","/")) for p in prompts):
            raise ValueError("unsafe prompt")
        tot+=len(prompts)
    if tot!=64:raise ValueError("invalid total")
    return manifest["groups"]

def stage_project(src,dst):
    if not (src/"chat.py").is_file():raise ValueError("missing chat.py")
    def ignore(directory,names):
        return {n for n in names if n in SKIP or n.endswith((".pt",".pth",".ckpt")) or
                (Path(directory)/n).is_symlink()}
    shutil.copytree(src,dst,ignore=ignore,symlinks=False)
    if not (dst/"chat.py").is_file():raise ValueError("missing staged chat.py")
    # Runtime's fixed relative model path may be referenced in default args;
    # explicit --model and --tokenizer below pin actual source assets.
    (dst/"model").mkdir(exist_ok=True)
    (dst/"results").mkdir(exist_ok=True)

def read_turns(output,prompts):
    # chat.py prints 'You> ' before replies. On piped stdin the typed
    # prompts are not echoed, so align sections with submitted order.
    segments=re.split(r"(?m)(?:^|\n)You> ?",output)[1:]
    turns=[]
    for index,p in enumerate(prompts):
        body=segments[index] if index<len(segments) else ""
        answer=re.search(r"(?m)^(AI|persona|wiki)> ?(.*)$",body)
        gate=re.search(r"(?m)^\[gate=.*$",body)
        turns.append({"question":p,"response":answer.group(2) if answer else None,
                      "response_prefix":answer.group(1) if answer else None,
                      "gate":gate.group(0) if gate else None,
                      "raw_segment":body,
                      "captured":bool(body)})
    return turns

def classify_failure(transcript, status):
    if "UnicodeDecodeError" in transcript or "UnicodeEncodeError" in transcript or "TextInputSequence must be str" in transcript or "\ufffd" in transcript:
        return "ENCODING_ERROR"
    if status == "TIMEOUT":return "TIMEOUT"
    if status == "PROCESS_FAILED":return "RUNTIME_ERROR"
    if not re.search(r"(?m)^(AI|persona|wiki)> ",transcript):return "NO_ANSWER"
    return None

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--manifest",required=True)
    ap.add_argument("--checkpoint",required=True)
    ap.add_argument("--tokenizer",required=True)
    ap.add_argument("--output",required=True)
    ap.add_argument("--timeout-per-group",type=int,default=240)
    ap.add_argument("--run",action="store_true",help="explicit opt-in to execute isolated benchmark")
    args=ap.parse_args()
    try:
        base=Path(__file__).resolve().parent
        manifest=Path(args.manifest).resolve(strict=True)
        model=Path(args.checkpoint).resolve(strict=True)
        tokenizer=Path(args.tokenizer).resolve(strict=True)
        dest=Path(args.output)
        if not all(p.is_file() for p in (manifest,model,tokenizer)):raise ValueError("missing input")
        if dest.exists() or dest.is_symlink():raise ValueError("output already exists")
        if args.timeout_per_group<1:raise ValueError("invalid timeout")
        groups=validate(json.loads(manifest.read_text(encoding="utf-8")))
        if not args.run:
            print(json.dumps({"ready":True,"groups":len(groups),"prompts":64,
                              "execute":False,"use_--run":True},ensure_ascii=False))
            return
        before_model_sha=sha(model)
        results=[]
        with tempfile.TemporaryDirectory(prefix="llm-cha-benchmark-") as folder:
            root=Path(folder)/"LLM_CHA"
            stage_project(base,root)
            for group in groups:
                prompts=group["prompts"]
                payload="\n".join(prompts+["/exit"])+"\n"
                cmd=[sys.executable,str(root/"chat.py"),
                     "--model",str(model),"--tokenizer",str(tokenizer),
                     "--no-learn"]
                try:
                    proc=subprocess.run(cmd,input=payload,text=True,encoding="utf-8",
                        errors="strict",cwd=root,stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,timeout=args.timeout_per_group,
                        env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1",
                             "PYTHONIOENCODING":"utf-8", "PYTHONUTF8":"1"})
                    transcript=proc.stdout
                    rc=proc.returncode
                    status="FINISHED" if rc==0 else "PROCESS_FAILED"
                except subprocess.TimeoutExpired as exc:
                    transcript=(exc.stdout or b"")
                    if isinstance(transcript,bytes):transcript=transcript.decode("utf-8","replace")
                    rc=None;status="TIMEOUT"
                failure=classify_failure(transcript,status)
                if status=="FINISHED" and failure is not None:status="CAPTURE_FAILED"
                results.append({"id":group["id"],"mode":group["mode"],
                                "status":status,"returncode":rc,"failure_category":failure,
                                "turns":read_turns(transcript,prompts),
                                "transcript":transcript})
                if len(results)==1 and status!="FINISHED":
                    print("first-case preflight failed; remaining cases skipped",file=sys.stderr)
                    break
        after_model_sha=sha(model)
        if before_model_sha!=after_model_sha:raise ValueError("source checkpoint changed during evaluation")
        report={"version":"v0.4.28.4","evaluation":"DEVELOPMENT_ONLY_NOT_HOLDOUT",
                "isolated_copy":True,"training_commands_sent":False,
                "checkpoint_sha256":sha(model),"tokenizer_sha256":sha(tokenizer),
                "manifest_sha256":sha(manifest),"checkpoint_path":str(model),
                "runtime":"chat.py --no-learn","groups":results,
                "passed_groups":sum(x["status"]=="FINISHED" for x in results)}
        dest.parent.mkdir(parents=True,exist_ok=True)
        with dest.open("x",encoding="utf-8") as f:
            json.dump(report,f,ensure_ascii=False,indent=2)
        print(json.dumps({"groups":len(results),"passed_groups":report["passed_groups"],
                          "output":str(dest)},ensure_ascii=False))
        if report["passed_groups"]!=56:sys.exit(2)
    except (OSError,ValueError,json.JSONDecodeError) as exc:
        ap.exit(1,f"benchmark capture failed: {exc}\n")
if __name__=="__main__":main()

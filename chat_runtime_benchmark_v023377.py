"""v0.2.33.77 experimental isolated chat.py subprocess benchmark.

Runs chat.py inside a temporary copy of the *project source and data*.
The original checkout must be a local folder; the benchmark never starts
chat.py in the source checkout. A writable report is written to --out.
Not a security boundary (Python can execute arbitrary side effects).
"""
import argparse,json,os,re,shutil,subprocess,sys,tempfile,time
from pathlib import Path
from runtime_startup_preflight_v0233772 import preflight

SCENARIOS=(
    ("greeting","こんにちは",r"AI>\s*こんにちは。",r"response-quality=REPAIRED"),
    ("mixed_truth","こんにちは、宇宙について教えて",r"multi-intent=GREETING_PLUS_KNOWLEDGE",r"truth-aware-corpus=BLOCK"),
    ("corpus_truth","宇宙とは",r"truth-aware-corpus=BLOCK",r"AI>\s*未学習です"),
    ("reference","昨日の続き",r"multi-intent=REFERENCE_CLARIFY",r"どの実験・話題の続き"),
)

def ensure_source(path):
    root=Path(path).resolve()
    if not (root/"chat.py").is_file():raise ValueError("missing_chat.py")
    if not (root/"model").is_dir():raise ValueError("missing_model_directory")
    if not (root/"data").is_dir():raise ValueError("missing_data_directory")
    return root

def isolated_copy(root,target):
    # Copy the exact checkout structure, including relative imports and data.
    # No symlinks: prevent accidentally following links to mutable originals.
    ignored=shutil.ignore_patterns(".git",".venv","venv","__pycache__","*.pyc",
        "results","*.sqlite3-wal","*.sqlite3-shm")
    if any(x.is_symlink() for x in root.rglob("*")):
        raise ValueError("symlinks_are_not_supported_for_isolation")
    shutil.copytree(root,target,ignore=ignored,symlinks=False)
    if not (target/"chat.py").is_file():raise ValueError("incomplete_sandbox")
    return target

def evaluate_transcript(stdout,returncode):
    # Python input() prints the prompt but piped stdin is not echoed.
    # Match *ordered* prompt-delimited output, never pretend user text was
    # present in the captured transcript.
    turns=re.split(r"You>\s?",stdout)[1:]
    results=[]
    for index,(cid,query,*patterns) in enumerate(SCENARIOS):
        if index>=len(turns):
            results.append({"id":cid,"passed":False,"reason":"turn_not_located",
                            "expected_patterns":list(patterns)})
            continue
        block=turns[index]
        missing=[p for p in patterns if re.search(p,block) is None]
        results.append({"id":cid,"passed":not missing,
                        "reason":"missing_patterns" if missing else "matched",
                        "missing_patterns":missing})
    return {"process_returncode":returncode,"cases":results,
            "passed":sum(bool(x["passed"]) for x in results),"total":len(results)}

def diagnose_failure(stderr, stdout, returncode, timed_out=False):
    """Separate setup/runtime failure from genuine policy mismatch."""
    if timed_out:
        return {"phase":"TIMEOUT","reason":"subprocess_timeout"}
    if returncode not in (0,None):
        if "Traceback (most recent call last)" in stderr:
            lines=[line.strip() for line in stderr.splitlines() if line.strip()]
            return {"phase":"STARTUP_OR_RUNTIME_ERROR","reason":"python_exception",
                    "exception_line":lines[-1] if lines else ""}
        if "can't open file" in stderr or "No module named" in stderr:
            return {"phase":"STARTUP_ERROR","reason":"missing_script_or_dependency"}
        return {"phase":"STARTUP_OR_RUNTIME_ERROR","reason":"nonzero_exit"}
    if "You>" not in stdout:
        return {"phase":"STARTUP_ERROR","reason":"no_chat_prompt"}
    return {"phase":"EVALUATION","reason":"process_completed"}

def preflight_failure(checks,reason):
    return {"version":"v0.2.33.77.2","kind":"isolated-chat-subprocess",
            "process_returncode":None,"passed":0,"total":len(SCENARIOS),
            "cases":[{"id":item[0],"passed":False,"reason":"not_evaluated_preflight_failure"}
                     for item in SCENARIOS],
            "diagnostic":{"phase":"PREFLIGHT_ERROR","reason":reason},
            "preflight":checks,"stdout_tail":"","stderr_tail":""}

def run(source,timeout=180):
    root=ensure_source(source)
    startup_checks=preflight(root)
    if not startup_checks["ok"]:
        return preflight_failure(startup_checks,"required_asset_or_dependency_missing")
    with tempfile.TemporaryDirectory(prefix="llm_cha_v023377_") as folder:
        target=isolated_copy(root,Path(folder)/"checkout")
        copied_checks=preflight(target)
        if not copied_checks["ok"]:
            return preflight_failure(copied_checks,"copied_assets_missing")
        commands=[x[1] for x in SCENARIOS]+["/exit"]
        args=[sys.executable,"-u","chat.py","--session-reference-memory",
              "--max-new-tokens","64"]
        started=time.monotonic()
        timed_out=False
        try:
            result=subprocess.run(args,input="\n".join(commands)+"\n",text=True,
                 encoding="utf-8",errors="replace",capture_output=True,
                 cwd=target,timeout=timeout,check=False,env={**os.environ,
                 "PYTHONDONTWRITEBYTECODE":"1"})
            stdout=result.stdout
            stderr=result.stderr
            status=result.returncode
        except subprocess.TimeoutExpired as exc:
            timed_out=True
            stdout=(exc.stdout or b"").decode("utf-8",errors="replace") if isinstance(exc.stdout,bytes) else (exc.stdout or "")
            stderr=(exc.stderr or b"").decode("utf-8",errors="replace") if isinstance(exc.stderr,bytes) else (exc.stderr or "")
            status=None
        # Excerpts intentionally may include model output, not private sources.
        report=evaluate_transcript(stdout,status)
        report["diagnostic"]=diagnose_failure(stderr,stdout,status,timed_out)
        if report["diagnostic"]["phase"]!="EVALUATION":
            for case in report["cases"]:
                case["passed"]=False
                case["reason"]="not_evaluated_runtime_failure"
            report["passed"]=0
        report.update({"version":"v0.2.33.77.2","kind":"isolated-chat-subprocess",
         "preflight":copied_checks,
         "elapsed_seconds":round(time.monotonic()-started,2),
         "stdout_tail":stdout[-12000:],"stderr_tail":stderr[-4000:],
         "limitations":"Not a security boundary; assertions depend on transcript format and local truth states."})
        return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",default=".")
    p.add_argument("--out",default="results/chat_runtime_v023377.json")
    p.add_argument("--timeout",type=int,default=180)
    p.add_argument("--run",action="store_true",help="Explicitly authorize a copied-checkout chat subprocess")
    a=p.parse_args()
    if not a.run:
        print("DRY RUN: no subprocess started. Use --run to execute in temporary checkout.")
        return 0
    if a.timeout<10: p.error("--timeout must be at least 10 seconds")
    report=run(a.source,a.timeout)
    path=Path(a.out);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print(json.dumps({k:report[k] for k in ("kind","passed","total","process_returncode","elapsed_seconds")},
         ensure_ascii=False,indent=2))
    print("diagnostic:",json.dumps(report["diagnostic"],ensure_ascii=False))
    print("preflight:",json.dumps(report.get("preflight"),ensure_ascii=False))
    if report["diagnostic"]["phase"]!="EVALUATION":
        print("stderr_tail:",report["stderr_tail"][-2500:])
    print("report:",path)
    return 0 if report["passed"]==report["total"] and report["process_returncode"]==0 else 1
if __name__=="__main__":sys.exit(main())

"""Experimental conversation generalization probes, separate from v0.2.33.78 acceptance."""
import argparse,json,re,subprocess,sys,tempfile,time
from pathlib import Path
from chat_runtime_benchmark_v023377 import child_environment,diagnose_failure,ensure_source,isolated_copy
from runtime_startup_preflight_v0233772 import preflight

# No gold standard has been established for these probes; report observations,
# not claimed accuracy. Each run uses a fresh temporary checkout.
PROBES=(
    ("greeting_paraphrase","やあ","greeting"),
    ("greeting_repeat","こんにちは","greeting"),
    ("topic_intro","宇宙について教えて","knowledge"),
    ("topic_followup","もう少し詳しく","context_followup"),
    ("known_definition","GPUとは","knowledge"),
    ("unknown_definition","架空概念XQZとは","unknown"),
    ("thanks","ありがとう","acknowledgement"),
    ("reference_ambiguity","あの実験の続き","reference"),
)
REJECTION_RE=re.compile(r"未学習です|truth-aware-corpus=BLOCK|gate=UNKNOWN")
ROUTE_RE=re.compile(r"(?:multi-intent|intent|route|truth-aware-corpus)=[^,\]\n]+")
AI_RE=re.compile(r"AI>\s*([^\r\n]*)")

def evaluate(stdout,returncode,probes=PROBES):
    blocks=re.split(r"You>\s?",stdout)[1:]
    results=[]
    for index,(name,query,kind) in enumerate(probes):
        block=blocks[index] if index<len(blocks) else ""
        m=AI_RE.search(block)
        answer=m.group(1).strip() if m else None
        results.append({
            "id":name,"query":query,"category":kind,
            "observed":bool(block),"answer":answer,
            "answer_present":bool(answer),
            "rejected":bool(REJECTION_RE.search(block)) if block else None,
            "route_markers":ROUTE_RE.findall(block)[:8],
            "generic_fallback":answer in ("未学習です","わかりません","こんにちは。") if answer else None,
            "raw_excerpt":block[:600]})
    return {"process_returncode":returncode,"probes":results,
            "observed":sum(x["observed"] for x in results),"total":len(results),
            "nonempty_answers":sum(x["answer_present"] for x in results),
            "warning":"Exploratory observations only; no semantic gold labels or pass rate."}

def run(source=".",timeout=240):
    root=ensure_source(source)
    with tempfile.TemporaryDirectory(prefix="llm_cha_v023379_") as tmp:
        target=isolated_copy(root,Path(tmp)/"checkout")
        checks=preflight(target)
        if not checks["ok"]:
            return {"version":"v0.2.33.79","diagnostic":{"phase":"PREFLIGHT_ERROR"},
                    "preflight":checks,"probes":[],"observed":0,"total":len(PROBES)}
        started=time.monotonic()
        timed_out=False
        try:
            p=subprocess.run([sys.executable,"-u","chat.py",
                "--session-reference-memory","--max-new-tokens","64"],
                input="\n".join(x[1] for x in PROBES)+"\n/exit\n",
                text=True,encoding="utf-8",errors="strict",capture_output=True,
                cwd=target,timeout=timeout,check=False,env=child_environment())
            stdout,stderr,status=p.stdout,p.stderr,p.returncode
        except subprocess.TimeoutExpired as exc:
            timed_out=True
            stdout=exc.stdout or b""
            stderr=exc.stderr or b""
            if isinstance(stdout,bytes):stdout=stdout.decode("utf-8","replace")
            if isinstance(stderr,bytes):stderr=stderr.decode("utf-8","replace")
            status=None
        report=evaluate(stdout,status)
        report.update({"version":"v0.2.33.79","kind":"conversation-generalization-observations",
          "diagnostic":diagnose_failure(stderr,stdout,status,timed_out),
          "preflight":checks,"elapsed_seconds":round(time.monotonic()-started,2),
          "stderr_tail":stderr[-4000:],"stdout_tail":stdout[-12000:]})
        return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--run",action="store_true")
    p.add_argument("--source",default=".")
    p.add_argument("--timeout",type=int,default=240)
    p.add_argument("--out",default="results/conversation_generalization_v023379.json")
    a=p.parse_args()
    if not a.run:
        print("DRY RUN: use --run to start exploratory GPU benchmark")
        return 0
    if a.timeout<10:p.error("--timeout must be >= 10")
    report=run(a.source,a.timeout)
    out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:report.get(k) for k in ("version","observed","total","nonempty_answers","process_returncode","diagnostic")},ensure_ascii=False,indent=2))
    print("report:",out)
    return 0 if report.get("process_returncode")==0 and report.get("observed")==report.get("total") else 1

if __name__=="__main__":sys.exit(main())

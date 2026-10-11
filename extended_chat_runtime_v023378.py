"""v0.2.33.78 exploratory multi-turn GPU runtime benchmark.

Fixed acceptance cases are separated from exploratory observations.
Runs only with --run in a copied checkout with UTF-8 child subprocess.
"""
import argparse
import json
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from chat_runtime_benchmark_v023377 import (
    SCENARIOS, child_environment, diagnose_failure, ensure_source, isolated_copy,
)
from runtime_startup_preflight_v0233772 import preflight

# A fresh copied checkout is used per run. All expectations are transcript
# observations, not claims of semantic correctness or factual truth.
EXTRA_CASES = (
    ("reference_variant", "あの実験", "acceptance",
     (r"(?:multi-intent|speech-act)=REFERENCE_CLARIFY",),
     (r"AI>\s*どの実験・話題の続き",)),
    ("mixed_variant", "こんにちは、宇宙とは", "exploratory",
     (r"multi-intent=GREETING_PLUS_KNOWLEDGE",),
     (r"truth-aware-corpus=BLOCK", r"AI>\s*未学習です")),
    ("greeting_repeat", "こんにちは", "exploratory",
     (r"intent=greeting",),
     (r"AI>\s*こんにちは。",)),
    ("thanks", "ありがとう", "exploratory", (), ()),
)
BASE_CASES = (
    ("greeting", "こんにちは", "acceptance",
     (r"response-quality=REPAIRED",r"intent=greeting"),
     (r"AI>\s*こんにちは。",)),
    ("mixed_truth", "こんにちは、宇宙について教えて", "acceptance",
     (r"multi-intent=GREETING_PLUS_KNOWLEDGE",r"truth-aware-corpus=BLOCK"),
     (r"AI>\s*未学習です",)),
    ("corpus_truth", "宇宙とは", "acceptance",
     (r"truth-aware-corpus=BLOCK",),
     (r"AI>\s*未学習です",)),
    ("reference", "昨日の続き", "acceptance",
     (r"multi-intent=REFERENCE_CLARIFY",),
     (r"AI>\s*どの実験・話題の続き",)),
)
assert tuple(x[0] for x in BASE_CASES) == tuple(x[0] for x in SCENARIOS)
CASES=BASE_CASES+EXTRA_CASES

def evaluate(stdout, returncode, cases=CASES):
    blocks=re.split(r"You>\s?",stdout)[1:]
    results=[]
    for i,(name,query,tier,route_patterns,answer_patterns) in enumerate(cases):
        if i >= len(blocks):
            route_missing=list(route_patterns)
            answer_missing=list(answer_patterns)
            observed=False
        else:
            observed=True
            route_missing=[x for x in route_patterns if not re.search(x,blocks[i])]
            answer_missing=[x for x in answer_patterns if not re.search(x,blocks[i])]
        results.append({
            "id":name,"query":query,"tier":tier,"observed":observed,
            "route_pass":observed and not route_missing if route_patterns else None,
            "answer_pass":observed and not answer_missing if answer_patterns else None,
            "route_missing":route_missing,"answer_missing":answer_missing,
            "preview":blocks[i][:350] if observed else "",
        })
    required=[c for c in results if c["tier"]=="acceptance"]
    acceptance_pass=all(
        c["observed"] and c["route_pass"] is True and c["answer_pass"] is True
        for c in required)
    return {"process_returncode":returncode,"cases":results,
            "acceptance_pass":acceptance_pass and returncode==0,
            "acceptance_total":len(required),
            "acceptance_matched":sum(c["observed"] and c["route_pass"] is True and c["answer_pass"] is True for c in required),
            "exploratory_total":len(results)-len(required)}

def run(source=".",timeout=240):
    root=ensure_source(source)
    with tempfile.TemporaryDirectory(prefix="llm_cha_v023378_") as folder:
        target=isolated_copy(root,Path(folder)/"checkout")
        checks=preflight(target)
        if not checks["ok"]:
            return {"version":"v0.2.33.78","kind":"extended-runtime",
                    "diagnostic":{"phase":"PREFLIGHT_ERROR","reason":"copied_assets_missing"},
                    "preflight":checks,"acceptance_pass":False,"cases":[]}
        commands=[x[1] for x in CASES]+["/exit"]
        started=time.monotonic()
        timed_out=False
        try:
            result=subprocess.run(
                [sys.executable,"-u","chat.py","--session-reference-memory",
                 "--max-new-tokens","64"],
                input="\n".join(commands)+"\n",text=True,encoding="utf-8",
                errors="strict",capture_output=True,cwd=target,timeout=timeout,
                env=child_environment(),check=False)
            stdout,stderr,status=result.stdout,result.stderr,result.returncode
        except subprocess.TimeoutExpired as exc:
            timed_out=True
            stdout=exc.stdout or b""
            stderr=exc.stderr or b""
            if isinstance(stdout,bytes):stdout=stdout.decode("utf-8","replace")
            if isinstance(stderr,bytes):stderr=stderr.decode("utf-8","replace")
            status=None
        report=evaluate(stdout,status)
        report["diagnostic"]=diagnose_failure(stderr,stdout,status,timed_out)
        if report["diagnostic"]["phase"]!="EVALUATION":
            report["acceptance_pass"]=False
        report.update({"version":"v0.2.33.78","kind":"extended-runtime",
                       "elapsed_seconds":round(time.monotonic()-started,2),
                       "preflight":checks,"stdout_tail":stdout[-16000:],
                       "stderr_tail":stderr[-4000:],
                       "limits":"Exploratory cases have no pass/fail acceptance threshold; regex checks are not semantic quality measurements."})
        return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--run",action="store_true")
    p.add_argument("--source",default=".")
    p.add_argument("--timeout",type=int,default=240)
    p.add_argument("--out",default="results/extended_chat_runtime_v023378.json")
    a=p.parse_args()
    if not a.run:
        print("DRY RUN: use --run for GPU evaluation")
        return 0
    if a.timeout<10:p.error("--timeout must be >= 10")
    report=run(a.source,a.timeout)
    target=Path(a.out)
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:report.get(k) for k in ("version","acceptance_matched",
          "acceptance_total","acceptance_pass","exploratory_total","process_returncode")},
          ensure_ascii=False,indent=2))
    print("diagnostic:",report["diagnostic"])
    print("report:",target)
    return 0 if report["acceptance_pass"] else 1

if __name__=="__main__":
    sys.exit(main())

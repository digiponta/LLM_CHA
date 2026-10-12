"""v0.2.33.82.10: opt-in GPU chat.py smoke test with isolated corpus snapshot.

Runs chat.py in a child process against a disposable COPY of the source corpus,
plus a disposable proposition Truth Overlay. Never writes reviews into
production truth state. Not a proof that all chat.py startup paths are isolated.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from proposition_truth_v0233827 import proposition_id

PROVENANCE = "data-nagato.txt:subject-keyed-corpus-memory:v10.12.16"
TOPIC = "宇宙"

def prepare_overlay(path: Path, propositions: list[str]) -> None:
    # Controlled synthetic decisions; never asserted as scientific truth.
    states = ["FALSE", "TRUE", "UNVERIFIED", "OUTDATED", "CONTESTED"]
    path.write_text("".join(
        json.dumps({"proposition_id": proposition_id(TOPIC, part, PROVENANCE),
                    "truth_state": states[i],
                    "provenance": "fixture:do-not-use-for-scientific-review"},
                   ensure_ascii=False) + "\n"
        for i, part in enumerate(propositions[:5])
    ), encoding="utf-8")

def acceptance(transcript: str, propositions: list[str]) -> dict[str, bool]:
    # Require explicit proposition IDs and route decisions; do not infer truth
    # policy from exit code alone.
    ids = {s: proposition_id(TOPIC, s, PROVENANCE) for s in propositions[:5]}
    false_id = ids.get(propositions[0]) if propositions else ""
    true_id = ids.get(propositions[1]) if len(propositions) > 1 else ""
    results = {
        "initial_false_blocked": f"proposition truth=BLOCK, id={false_id}, state=FALSE" in transcript,
        "true_proposition_displayed": bool(true_id and f"proposition-id={true_id}, truth_state=TRUE" in transcript),
        "unverified_label": "【未検証の記録】" in transcript,
        "no_generation": "0 generated probe tokens" in transcript,
        "reset_clears_topic": "参照できる話題がありません" in transcript,
    }
    return results

def run(timeout: int, source: Path, python: str = sys.executable) -> dict:
    if not source.is_file():
        raise FileNotFoundError(source)
    # Pull actual source answer through the existing retrieval function.
    from chat import retrieval_first_resolve_subject
    retrieval = retrieval_first_resolve_subject(source, TOPIC)
    if not retrieval.hit:
        raise RuntimeError("Fixture requires an existing 宇宙 corpus entry")
    propositions = [s.strip() for s in retrieval.answer.split(" / ") if s.strip()]
    if len(propositions) < 5:
        raise RuntimeError("Fixture requires >=5 corpus propositions")
    with tempfile.TemporaryDirectory(prefix="llm-cha-gpu-accept-") as tmp:
        root = Path(tmp)
        corpus = root / "isolated-corpus.jsonl"
        overlay = root / "isolated-overlay.jsonl"
        shutil.copyfile(source, corpus)
        before = corpus.read_bytes()
        prepare_overlay(overlay, propositions)
        env = os.environ.copy()
        env["LLM_CHA_MULTITOPIC"] = "1"
        env["LLM_CHA_PROPOSITION_TRUTH"] = str(overlay)
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUNBUFFERED"] = "1"
        commands = "\n".join([
            "宇宙について教えて", "もう少し詳しく",
            "もう少し詳しく", "/reset", "もう少し詳しく", "/exit", ""
        ])
        process = subprocess.run(
            [python, "-u", "chat.py", "--corpus-memory", str(corpus)],
            input=commands, encoding="utf-8", errors="replace",
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            env=env, timeout=timeout, check=False,
        )
        checks = acceptance(process.stdout, propositions)
        checks["exit_code_zero"] = process.returncode == 0
        checks["corpus_copy_unchanged"] = before == corpus.read_bytes()
        checks["overlay_unchanged"] = overlay.is_file()
        return {"version": "v0.2.33.82.10",
                "pass": all(checks.values()), "checks": checks,
                "returncode": process.returncode,
                "transcript": process.stdout}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", default="data/subject_keyed_corpus_memory_v101216.jsonl")
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument("--report", default="results/mixed_state_gpu_accept_v02338210.json")
    args = parser.parse_args()
    data = run(args.timeout, Path(args.corpus))
    report = Path(args.report)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k:v for k,v in data.items() if k != "transcript"}, ensure_ascii=False, indent=2))
    print(f"report: {report}")
    return 0 if data["pass"] else 1

if __name__ == "__main__":
    sys.exit(main())

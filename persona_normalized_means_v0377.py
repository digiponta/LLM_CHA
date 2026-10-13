"""v0.3.7.7 normalized persona means roles, indexed from v0.3.7.6 candidates.

Candidate answers quote the original (no unlicensed causative); provenance and
uncertainty are explicit. Read-only, no automatic fact promotion.
"""
from __future__ import annotations
from pathlib import Path
from persona_means_audit_v0376 import extract
from persona_means_index_v0375 import query_focus

def normalized_rows(source: str | Path):
    rows=[]
    for item in extract(source):
        rows.append({
            "subject":item["subject"],"means":item["means"],"predicate":item["predicate"],
            "relation":"MEANS_OF","source":item["source"],"line":item["line"],
            "segment":item["segment"],"original":item["original"],
            "derived":item["derived"],"renderable":item["derived"] is not None,
            "factual_truth":"NOT_ASSESSED","certainty":"CANDIDATE_UNREVIEWED"
        })
    return rows

def lookup(source: str | Path, question: str):
    intent=query_focus(question)
    if intent is None:
        return None
    role,focus=intent
    rows=normalized_rows(source)
    matches=[row for row in rows if row["means" if role=="means" else "subject"]==focus]
    if not matches:
        return None
    row=matches[0]
    # For unreviewed candidates, quoting original is safer than claiming
    # an inferred causation or a new direct assertion.
    if not row["renderable"]:
        answer="この人格の原文には、次の記述があります。「"+row["original"]+"」"
        mode="SOURCE_QUOTE"
    else:
        answer=row["derived"] if role=="means" else row["original"]
        mode="LICENSED_PARAPHRASE" if role=="means" else "SOURCE_QUOTE"
    return {**row,"role":role,"focus":focus,"answer":answer,"mode":mode,
            "count":len(matches)}

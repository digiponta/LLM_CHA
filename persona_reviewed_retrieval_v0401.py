"""v0.4.1 opt-in reviewed-only persona MEANS_OF retrieval.

Human review is semantic-role adjudication, never scientific truth certification.
Invalid/missing reviews fail closed. No file writes.
"""
from __future__ import annotations
from pathlib import Path
from persona_review_score_v0400 import score
from persona_means_index_v0375 import query_focus
from persona_normalized_means_v0377 import normalized_rows
from persona_review_v0378 import candidate_id

def reviewed_lookup(source, csv_path, question):
    intent=query_focus(question)
    if intent is None:return None
    reviewed=score(source,csv_path)  # validates exact IDs, source, roles, verdicts
    allowed={x["id"] for x in reviewed["accepted_for_future_review_only"]}
    role,focus=intent
    selected=[]
    for row in normalized_rows(source):
        id_row={"source":row["source"],"line":row["line"],
                "segment":row["segment"],"original":row["original"]}
        if candidate_id(id_row) not in allowed:continue
        if row["means" if role=="means" else "subject"] !=focus:continue
        selected.append(row)
    if len(selected)!=1:
        return None  # no match or ambiguous multiple matches: fail closed
    row=selected[0]
    # Quote verbatim even if v0.3.7.2 permits a causative transformation.
    return {"answer":"この人格の原文には、次の記述があります。「"+row["original"]+"」",
            "line":row["line"],"segment":row["segment"],"role":role,
            "focus":focus,"mode":"REVIEWED_SOURCE_QUOTE","factual_truth":"NOT_ASSESSED",
            "subject":row["subject"],"means":row["means"]}

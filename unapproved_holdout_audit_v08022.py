"""v0.8.0.22: read-only holdout provenance and overlap audit.

Lexical overlap flags are warnings, not evidence of semantic independence.
"""
import json
import re
from pathlib import Path
from difflib import SequenceMatcher
from unapproved_llm_intake_v074446 import _read

KINDS=("UNSEEN_FACT","PARAPHRASE")
def normalize(text):
    return re.sub(r"\s+","",str(text or "")).casefold().strip("。！？!? ")
def audit(path,store,similarity_threshold=0.78):
    p=Path(path)
    if not p.exists():
        return {"status":"MISSING_DATA","record_count":0,"usable_for_formal_evaluation":False}
    data=json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(data,dict) or not isinstance(data.get("records"),list):
        return {"status":"INVALID_DATA","record_count":0,"usable_for_formal_evaluation":False}
    training=_read(store)["candidates"]
    training_texts=[normalize(r.get("natural_language","")) for r in training]
    training_subjects={normalize(r.get("subject","")) for r in training}
    details=[]
    seen=set()
    for row in data["records"]:
        if not isinstance(row,dict):
            details.append({"status":"INVALID_ROW","flags":["INVALID_ROW"]})
            continue
        rid=str(row.get("id",""))
        question=normalize(row.get("question"))
        answer=normalize(row.get("reference_answer"))
        kind=row.get("evaluation_kind")
        flags=[]
        if kind not in KINDS: flags.append("EVALUATION_KIND_REQUIRED")
        if not rid or rid in seen:flags.append("MISSING_OR_DUPLICATE_ID")
        seen.add(rid)
        if any(token in (rid+question+answer).casefold() for token in ("replace-with","ここに","sample","example")):
            flags.append("PLACEHOLDER")
        if not row.get("source_url") or not row.get("source_excerpt"):flags.append("PROVENANCE_INCOMPLETE")
        if kind=="UNSEEN_FACT" and any(sub and sub in question for sub in training_subjects):
            flags.append("TRAINED_SUBJECT_IN_UNSEEN_FACT")
        similarity=max((SequenceMatcher(None,answer,t).ratio()
                        for t in training_texts if t),default=0.0)
        if similarity>=similarity_threshold:
            flags.append("LEXICAL_ANSWER_OVERLAP")
        details.append({"id":rid,"evaluation_kind":kind,"flags":flags,
                        "max_training_answer_similarity":round(similarity,4)})
    blocking=any(row["flags"] for row in details)
    counts={k:sum(row.get("evaluation_kind")==k for row in details) for k in KINDS}
    return {"status":"REVIEW_REQUIRED" if blocking else "AUDITED",
            "record_count":len(details),"kind_counts":counts,
            "details":details,"source_attested":data.get("independent_source_attested") is True,
            "semantic_independence_verified":False,
            "usable_for_formal_evaluation":False,
            "note":"Read-only audit; a separate formal gate controls scoring."}

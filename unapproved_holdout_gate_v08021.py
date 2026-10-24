"""v0.8.0.21: fail-closed formal holdout readiness gate.

Attestation is a declaration, not proof of statistical independence.
"""
from unapproved_holdout_v08020 import validate_holdout

PLACEHOLDERS=("replace-with","ここに","sample","example","テスト用の仮")
def formal_holdout_gate(data,training_rows,checkpoint_ids,min_records=5):
    reasons=[]
    if not isinstance(data,dict):
        return {"status":"NOT_READY","reasons":["INVALID_FORMAT"],"validated_count":0}
    try:
        records=validate_holdout(data,training_rows,checkpoint_ids)
    except (ValueError,TypeError,KeyError) as exc:
        return {"status":"NOT_READY","reasons":[str(exc)],"validated_count":0}
    if data.get("independent_source_attested") is not True:
        reasons.append("SOURCE_INDEPENDENCE_NOT_ATTESTED")
    if len(records)<min_records:
        reasons.append("INSUFFICIENT_RECORDS")
    for i,row in enumerate(data["records"]):
        values=(row.get("id",""),row.get("question",""),row.get("reference_answer",""))
        if any(any(marker in v.casefold() for marker in PLACEHOLDERS) for v in values):
            reasons.append("PLACEHOLDER_RECORD:"+str(i))
        source=row.get("source_url")
        if not isinstance(source,str) or not source.startswith(("https://","http://")):
            reasons.append("SOURCE_MISSING:"+str(i))
        if not isinstance(row.get("source_excerpt"),str) or not row["source_excerpt"].strip():
            reasons.append("SOURCE_EXCERPT_MISSING:"+str(i))
    return {"status":"READY" if not reasons else "NOT_READY",
        "reasons":reasons,"validated_count":len(records),
        "min_records":min_records,"independence_verified":False}
